from typing import Any, Dict, List, Text, Union, Optional

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction
from rasa_sdk.events import UserUtteranceReverted
from rasa_sdk.events import SlotSet

import json
import datetime
import requests
import re

def getplace(value):
    result = False
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {"input": value, "inputtype": "textquery", "fields": "name,geometry",
              "key": "AIzaSyCGOJd4MqkT7XSmErgRVohfDB-IuAtNEPc", "lang": "en"}
    res = requests.get(url=url, params=params)
    jsontext = json.loads(res.text)
    if jsontext["status"] != "ZERO_RESULTS":
        lat = jsontext["candidates"][0]["geometry"]["location"]["lat"]
        lng = jsontext["candidates"][0]["geometry"]["location"]["lng"]
        result = jsontext["candidates"][0]["name"] + "[" + str(lat) + "," + str(lng) + "]"
    return result

class ActionGreetUser(Action):
    def name(self):
        return "action_greet"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_template("utter_greet", tracker)
        return [UserUtteranceReverted()]

class ActionRoute(Action):
    def name(self):
        return "action_route"

    def run(self, dispatcher, tracker, domain):
        print(tracker.latest_message['text'])
        text = tracker.latest_message['text']
        entities = tracker.latest_message['entities']
        location_to = ''
        location_from = ''
        location_sw = ''
        location_from_str = ''
        location_to_str = ''
        for entity in entities:
            if entity['entity'] == 'location_to':
                location_to = entity
            if entity['entity'] == 'location_from':
                location_from = entity
            if entity['entity'] == 'location_sw':
                location_sw = entity

        if location_sw != '':
            text = text.replace(location_sw['value'],'')

        if location_from != '' and location_to != '':
            if int(location_to['start']) > int(location_from['start']):
                location_from_str = text[location_from['end']:location_to['start']]
                location_to_str = text[location_to['end']:]
            else:
                location_to_str = text[location_to['end']:location_from['start']]
                location_from_str = text[location_from['end']:]
        elif location_to != '':
            location_from_str = text[:location_to['start']]
            location_to_str = text[location_to['end']:]

        punctuation = '!,;:"\'、，；?？*@#￥%……&（）()'
        location_from_str = re.sub(r'[{}]+'.format(punctuation), ' ', location_from_str).strip()
        location_to_str = re.sub(r'[{}]+'.format(punctuation), ' ', location_to_str).strip()
        dispatcher.utter_message(text='flow_route_' + location_from_str + '_' + location_to_str)
        return []

class ActionGettingThere(Action):
    def name(self):
        return "action_gettingthere"

    def run(self, dispatcher, tracker, domain):
        value = tracker.latest_message['text']
        pattern = re.compile('(\\[).*?(\\])')
        searchObj = pattern.search(value)
        if searchObj:
            gps = searchObj.group()
            url = "https://maps.googleapis.com/maps/api/geocode/json?key=AIzaSyCGOJd4MqkT7XSmErgRVohfDB-IuAtNEPc&latlng=" + gps.replace(
                '[', '').replace(']', '')
            res = requests.get(url=url)
            jsontext = json.loads(res.text)
            address = jsontext['results'][0]['formatted_address']
            print(address)
            dispatcher.utter_message(text='you are from ' + address + gps)
            return []
        elif len(value) > 1:
            url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
            params = {"input": value, "inputtype": "textquery", "fields": "name,geometry",
              "key": "AIzaSyCGOJd4MqkT7XSmErgRVohfDB-IuAtNEPc","lang":"en"}
            res = requests.get(url=url, params=params)
            jsontext = json.loads(res.text)
            if jsontext["status"] != "ZERO_RESULTS":
                lat = jsontext["candidates"][0]["geometry"]["location"]["lat"]
                lng = jsontext["candidates"][0]["geometry"]["location"]["lng"]
                dispatcher.utter_message(text='you are from ' + jsontext["candidates"][0]["name"] + "[" + str(lat)  + "," + str(lng) + "]")
                return []
            else:
                dispatcher.utter_message(template="utter_wrong_location")
                return []
        else:
            dispatcher.utter_message(template="utter_wrong_location")
            return []

class ActionEvent(Action):
    def name(self):
        return "action_event"

    def run(self, dispatcher, tracker, domain):
        #print("action_event")
        text = tracker.latest_message['text']
        starttime = 0
        endtime = 0
        list = tracker.latest_message['entities']
        is_month = False
        for item in list:
            if item['extractor'] == 'DucklingHTTPExtractor' and item['entity'] == 'time':
                if 'from' in item['value'] and 'to' in item['value']:
                    #print(item['value'])
                    starttime =  item['value']['from']
                    endtime = item['value']['to']
                elif 'grain' in item['additional_info'] and item['additional_info']['grain'] == 'day':
                    if starttime == 0:
                        starttime = item['value']
                    else:
                        endtime = item['value']
                elif 'grain' in item['additional_info'] and item['additional_info']['grain'] == 'month':
                    if starttime == 0:
                        starttime = item['value']
                        is_month = True

        #print(starttime)
        #print(endtime)
        if starttime != 0 and endtime != 0:
            starttime = starttime[:10]
            endtime = endtime[:10]
            if text.find('202'):
                year = datetime.datetime.now().year
                starttime = str(year) + starttime[4:10]

            endtime = datetime.datetime.strptime(endtime, '%Y-%m-%d')
            endtime = endtime - datetime.timedelta(days=1)
            endtime = endtime.strftime("%Y-%m-%d")
            endtime = str(year) + endtime[4:10]

            dispatcher.utter_message(text="flow_event_" + starttime + '_' + endtime)
        elif starttime != 0:
            if is_month:
                starttime = starttime[:10]
                print(starttime)
                starttime = datetime.datetime.strptime(starttime, '%Y-%m-%d')
                print(starttime)
                future_mouth_first = datetime.datetime(starttime.year, starttime.month + 1, 1, 23, 59, 59)
                print(future_mouth_first)
                endtime = future_mouth_first - datetime.timedelta(days=1)
                print(endtime)
                dispatcher.utter_message(text="flow_event_" + str(starttime)[:10] + '_' + str(endtime)[:10])
            else:
                starttime = starttime[:10]
                print(starttime)
                endtime = starttime
                print(endtime)
                dispatcher.utter_message(text="flow_event_" + starttime + '_' + endtime)

        return []

class ActionTransit(Action):
    def name(self):
        return "action_transit"

    def run(self, dispatcher, tracker, domain):
        text = tracker.latest_message['text']
        print(text)
        starttime = 0
        endtime = 0
        duration = 0
        result = 0
        endtime_minus_one_hour = False
        list = tracker.latest_message['entities']
        for item in list:
            if item['extractor'] == 'DucklingHTTPExtractor' and item['entity'] == 'time':
                if 'grain' in item['additional_info'] and (item['additional_info']['grain'] == 'hour' or item['additional_info']['grain'] == 'second'):
                    if starttime == 0:
                        starttime = item['value']
                    else:
                        endtime = item['value']
                elif 'to' in item['value'] and 'from' in item['value']:
                    endtime_minus_one_hour = True
                    starttime = item['value']['from']
                    endtime = item['value']['to']
            if item['extractor'] == 'DucklingHTTPExtractor' and item['entity'] == 'duration':
                duration = item['value']
        if starttime != 0 and endtime != 0:
            starttime = datetime.datetime.strptime(starttime[:19], '%Y-%m-%dT%H:%M:%S')
            isBreak = False
            if starttime.hour > 12:
                for item in list:
                    if item['extractor'] == 'DucklingHTTPExtractor' and item['entity'] == 'time':
                        if 'grain' in item['additional_info'] and item['additional_info']['grain'] == 'hour' and 'values' in item['additional_info']:
                            for value in item['additional_info']['values']:
                                if 'grain' in value and 'value' in value and value['grain'] == 'hour':
                                    tempTime = datetime.datetime.strptime(value['value'][:19], '%Y-%m-%dT%H:%M:%S')
                                    if tempTime.hour <= 12:
                                        starttime = tempTime
                                        isBreak = True
                                        break
                    if (isBreak):
                        break
            endtime = datetime.datetime.strptime(endtime[:19], '%Y-%m-%dT%H:%M:%S')
            if endtime_minus_one_hour:
                endtime = endtime - datetime.timedelta(hours=1)
            result = (endtime - starttime).seconds / 3600
            dispatcher.utter_message(text='inform_duration_' + str(result))
            return []
        elif duration != 0:
            dispatcher.utter_message(text='inform_duration_' + str(duration))
            return []
        else:
            print('enter in')
            pattern = re.compile(r'\d*\shour|\d*\shours|\d*\shrs')
            searchObj = pattern.search(text)
            if searchObj:
                duration = searchObj.group().replace('hours', '').replace('hour', '').replace('hrs', '')
                print(duration)
                dispatcher.utter_message(text='inform_duration_' + str(duration))
                return []
            pattern = re.compile(r'one day')
            searchObj = pattern.search(text)
            if searchObj:
                duration = 24
                print(duration)
                dispatcher.utter_message(text='inform_duration_' + str(duration))
                return []

            dispatcher.utter_message(template="utter_ask_duration")
            return []

class ActionMuseum(Action):
    def name(self):
        return "action_museum"

    def run(self, dispatcher, tracker, domain):
        value = tracker.latest_message['text']
        pattern = re.compile('(\\[).*?(\\])')
        searchObj = pattern.search(value)
        if searchObj:
            dispatcher.utter_message(text='flow_museum_' + searchObj.group())
            return []
        elif len(value) > 1:
            dispatcher.utter_message(text='flow_museum_' + value)
            return []
        else:
            dispatcher.utter_message(template="utter_wrong_location")
            return []

class ActionCityWalks(Action):
    def name(self):
        return "action_citywalks"

    def run(self, dispatcher, tracker, domain):
        value = tracker.latest_message['text']
        pattern = re.compile('(\\[).*?(\\])')
        searchObj = pattern.search(value)
        if searchObj:
            dispatcher.utter_message(text='flow_citywalks_' + searchObj.group())
            return []
        elif len(value) > 1:
            dispatcher.utter_message(text='flow_citywalks_' + value)
            return []
        else:
            dispatcher.utter_message(template="utter_wrong_location")
            return []

class ActionSightseeingLocation(Action):
    def name(self):
        return "action_sightseeinglocation"

    def run(self, dispatcher, tracker, domain):
        entities = tracker.latest_message['entities']
        if tracker.get_slot("sightseeing_district") == None:
            location = ''
            #print('entities')
            #print(entities)
            for entity in entities:
                if entity['entity'] == 'location':
                    location = entity['value']
            #print(location)
            if location != '':
                dispatcher.utter_message(template="utter_ask_sightseeing")
                return[SlotSet("sightseeing_district", location)]
            else:
                return[]
        else:
            sightseeing = tracker.latest_message['text']

            if sightseeing.lower() == 'key attractions':
                sightseeing = 'Key Attractions,熱門景點'
            elif sightseeing.lower() == 'great outdoors':
                sightseeing = 'Great Outdoors,戶外探索'
            elif sightseeing.lower() == 'local culture':
                sightseeing = 'Local Culture,在地文化'
            elif sightseeing.lower() == 'arts':
                sightseeing = 'Arts,藝文創意'
            elif sightseeing.lower() == 'museums':
                sightseeing = 'Museums,博物館'
            elif sightseeing.lower() == 'heritage & history':
                sightseeing = 'Heritage & History,歷史古蹟,HeritageHistory'
            elif sightseeing.lower() == 'thematic itineraries':
                sightseeing = 'Thematic Itineraries,主題路線'

            dispatcher.utter_message(
                text='flow_sightseeing_' + sightseeing + '_' + tracker.get_slot(
                    "sightseeing_district"))
            return [SlotSet("sightseeing_district")]

class ActionHiking(Action):
    def name(self):
        return "action_hiking"

    def run(self, dispatcher, tracker, domain):
        intent = tracker.latest_message['intent']['name']
        #print(intent)
        if intent == 'inform_duration':
            duration = tracker.latest_message['text']
            #print(duration)
            duration_list = ['within 2 hours','2-4','4-6','more than 6 hours']
            if duration.lower() in duration_list:
                dispatcher.utter_message(template="utter_ask_hiking_district")
                return [SlotSet("hiking_duration", duration)]

        elif intent == 'inform_location':
            location = tracker.latest_message['text']
            #print(location)
            dispatcher.utter_message(
                text='flow_hiking_' + tracker.get_slot("hiking_duration") + '_' + location)

class ActionSightseeing(Action):
    def name(self):
        return "action_sightseeing"

    def run(self, dispatcher, tracker, domain):
        intent = tracker.latest_message['intent']['name']
        #print(intent)
        if intent == 'sightseeing_flow' or intent == 'museum_flow':
            sightseeing = tracker.latest_message['text'].lower()
            #print(duration)
            sightseeing_list = ['key attractions','arts','great outdoors','local culture','heritage & history','thematic itineraries','museums']
            if sightseeing in sightseeing_list:
                if sightseeing == 'key attractions':
                    sightseeing = 'Key Attractions,熱門景點'
                elif sightseeing == 'great outdoors':
                    sightseeing = 'Great Outdoors,戶外探索'
                elif sightseeing == 'local culture':
                    sightseeing = 'Local Culture,在地文化'
                elif sightseeing == 'arts':
                    sightseeing = 'Arts,藝文創意'
                elif sightseeing == 'museums':
                    sightseeing = 'Museums,博物館'
                elif sightseeing == 'heritage & history':
                    sightseeing = 'Heritage & History,歷史古蹟'
                elif sightseeing == 'thematic itineraries':
                    sightseeing = 'Thematic Itineraries,主題路線'
                dispatcher.utter_message(template="utter_ask_sightseeing_district")
                return [SlotSet("sightseeing", sightseeing)]
        elif intent == 'inform_location':
            location = tracker.latest_message['text']
            sightseeing_district = ''
            pattern = re.compile('(\\[).*?(\\])')
            searchObj = pattern.search(location)
            if searchObj:
                sightseeing_district = searchObj.group()
            elif len(location) > 1:
                sightseeing_district = location

            if sightseeing_district == '':
                dispatcher.utter_message(template="utter_wrong_location")
            else:
                dispatcher.utter_message(
                    text='flow_sightseeing_' + tracker.get_slot("sightseeing") + '_' + location)
            return []

class ActionShoppingMall(Action):
    def name(self):
        return "action_shoppingmall"

    def run(self, dispatcher, tracker, domain):
        value = tracker.latest_message['text']
        pattern = re.compile('(\\[).*?(\\])')
        searchObj = pattern.search(value)
        if searchObj:
            dispatcher.utter_message(text='flow_shoppingmall_' + searchObj.group())
            return []
        elif len(value) > 1:
            dispatcher.utter_message(text='flow_shoppingmall_' + value)
            return []
        else:
            dispatcher.utter_message(template="utter_wrong_location")
            return []

class ActionDepartmentStore(Action):
    def name(self):
        return "action_departmentstore"

    def run(self, dispatcher, tracker, domain):
        value = tracker.latest_message['text']
        pattern = re.compile('(\\[).*?(\\])')
        searchObj = pattern.search(value)
        if searchObj:
            dispatcher.utter_message(text='flow_departmentstore_' + searchObj.group())
            return []
        elif len(value) > 1:
            dispatcher.utter_message(text='flow_departmentstore_' + value)
            return []
        else:
            dispatcher.utter_message(template="utter_wrong_location")
            return []

class TransitForm(FormAction):
    def name(self) -> Text:
        return "transit_form"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return ["duration"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        return {
            "duration": [self.from_entity(entity="duration"),self.from_text(intent=["inform_duration"])]
        }

    def validate_duration(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        text = tracker.latest_message['text']
        print(text)
        starttime = 0
        endtime = 0
        duration = 0
        result = 0
        endtime_minus_one_hour = False
        list = tracker.latest_message['entities']
        for item in list:
            if item['extractor'] == 'DucklingHTTPExtractor' and item['entity'] == 'time':
                if 'grain' in item['additional_info'] and (item['additional_info']['grain'] == 'hour' or item['additional_info']['grain'] == 'second'):
                    if starttime == 0:
                        starttime = item['value']
                    else:
                        endtime = item['value']
                elif 'to' in item['value'] and 'from' in item['value']:
                    endtime_minus_one_hour = True
                    starttime = item['value']['from']
                    endtime = item['value']['to']
            if item['extractor'] == 'DucklingHTTPExtractor' and item['entity'] == 'duration':
                duration = item['value']
        if starttime != 0 and endtime != 0:
            starttime = datetime.datetime.strptime(starttime[:19], '%Y-%m-%dT%H:%M:%S')
            isBreak = False
            if starttime.hour > 12:
                for item in list:
                    if item['extractor'] == 'DucklingHTTPExtractor' and item['entity'] == 'time':
                        if 'grain' in item['additional_info'] and item['additional_info'][
                            'grain'] == 'hour' and 'values' in item['additional_info']:
                            for value in item['additional_info']['values']:
                                if 'grain' in value and 'value' in value and value['grain'] == 'hour':
                                    tempTime = datetime.datetime.strptime(value['value'][:19], '%Y-%m-%dT%H:%M:%S')
                                    if tempTime.hour <= 12:
                                        starttime = tempTime
                                        isBreak = True
                                        break
                    if (isBreak):
                        break
            endtime = datetime.datetime.strptime(endtime[:19], '%Y-%m-%dT%H:%M:%S')
            if endtime_minus_one_hour:
                endtime = endtime - datetime.timedelta(hours=1)
            result = (endtime - starttime).seconds / 3600
            return {"duration": result}
        elif duration != 0:
            return {"duration": duration}
        else:
            pattern = re.compile(r'\d*\s*[hour|hours|hrs]')
            searchObj = pattern.search(text)
            if searchObj:
                duration = searchObj.group().replace('h', '')
                print(duration)
                return {"duration": duration}
            pattern = re.compile(r'one day')
            searchObj = pattern.search(text)
            if searchObj:
                duration = 24
                print(duration)
                return {"duration": duration}

            dispatcher.utter_message(template="utter_wrong_duration")
            return {"duration": None}

    def submit(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        dispatcher.utter_message(text='inform_duration_' + str(tracker.get_slot("duration")))
        return [SlotSet("duration")]

class SightseeingForm(FormAction):
    def name(self) -> Text:
        return "sightseeing_form"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return ["sightseeing","sightseeing_district"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        return {
            "sightseeing": [self.from_entity(entity="sightseeing"), self.from_text(intent=["museum_flow"])],
            "sightseeing_district": [self.from_entity(entity="location"), self.from_text(intent=["inform_location"])]
        }

    def validate_sightseeing(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        intent = tracker.latest_message['intent']['name']
        if intent == 'sightseeing_flow' and value.lower() not in ['key attractions','arts','great outdoors','local culture','heritage & history','thematic itineraries']:
            return {"sightseeing": None}
        else:
            if value.lower() == 'key attractions':
                value = 'Key Attractions,熱門景點'
            elif value.lower() == 'great outdoors':
                value = 'Great Outdoors,戶外探索'
            elif value.lower() == 'local culture':
                value = 'Local Culture,在地文化'
            elif value.lower() == 'arts':
                value = 'Arts,藝文創意'
            elif value.lower() == 'museums':
                value = 'Museums,博物館'
            elif value.lower() == 'heritage & history':
                value = 'Heritage & History,歷史古蹟'
            elif value.lower() == 'thematic itineraries':
                value = 'Thematic Itineraries,主題路線'
            return {"sightseeing": value}

    def validate_sightseeing_district(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        pattern = re.compile('(\\[).*?(\\])')
        searchObj = pattern.search(value)
        if searchObj:
            return {"sightseeing_district": searchObj.group()}
        elif len(value) > 1:
            return {"sightseeing_district": value}
        else:
            dispatcher.utter_message(template="utter_wrong_location")
            return {"sightseeing_district": None}

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        dispatcher.utter_message(text='flow_sightseeing_' + tracker.get_slot("sightseeing") + '_' + tracker.get_slot("sightseeing_district"))
        return [SlotSet("sightseeing"),SlotSet("sightseeing_district")]

class MuseumForm(FormAction):
    def name(self) -> Text:
        return "museum_form"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return ["museum_district"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        return {
            "museum_district": [self.from_entity(entity="location"), self.from_text(intent=["inform_location","kg"])],
        }

    def validate_museum_district(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        pattern = re.compile('(\\[).*?(\\])')
        searchObj = pattern.search(value)
        if searchObj:
            return {"museum_district": searchObj.group()}
        elif len(value) > 1:
            return {"museum_district": value}
        else:
            dispatcher.utter_message(template="utter_wrong_location")
            return {"museum_district": None}

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        dispatcher.utter_message(text='flow_museum_' + tracker.get_slot("museum_district"))
        return [SlotSet("museum_district")]

class HikingForm(FormAction):
    def name(self) -> Text:
        return "hiking_form"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return ["hiking_duration","hiking_district"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        return {
            "hiking_duration": [self.from_entity(entity="hiking_duration"), self.from_text(intent=["inform_duration"])],
            "hiking_district": [self.from_entity(entity="location"), self.from_text(intent=["inform_location","kg"])]
        }

    def validate_hiking_duration(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        return {"hiking_duration": value}

    def validate_hiking_district(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        if len(value) > 1:
            return {"hiking_district": value}
        else:
            dispatcher.utter_message(template="utter_wrong_location")
            return {"hiking_district": None}

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        dispatcher.utter_message(text='flow_hiking_' + tracker.get_slot("hiking_duration") + '_' + tracker.get_slot("hiking_district"))
        return [SlotSet("hiking_duration"),SlotSet("hiking_district")]

class ShoppingMallForm(FormAction):
    def name(self) -> Text:
        return "shoppingmall_form"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return ["shoppingmall_distict"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        return {
            "shoppingmall_distict": [self.from_entity(entity="location"), self.from_text(intent=["inform_location","kg"])],
        }

    def validate_shoppingmall_distict(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        pattern = re.compile('(\\[).*?(\\])')
        searchObj = pattern.search(value)
        if searchObj:
            return {"shoppingmall_distict": searchObj.group()}
        elif len(value) > 1:
            return {"shoppingmall_distict": value}
        else:
            return {"shoppingmall_distict": None}

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        dispatcher.utter_message(text='flow_shoppingmall_' + tracker.get_slot("shoppingmall_distict"))
        return [SlotSet("shoppingmall_distict")]

class DepartmentStoreForm(FormAction):
    def name(self) -> Text:
        return "departmentstore_form"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return ["departmentstore_distict"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        return {
            "departmentstore_distict": [self.from_entity(entity="location"), self.from_text(intent=["inform_location","kg"])],
        }

    def validate_departmentstore_distict(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        pattern = re.compile('(\\[).*?(\\])')
        searchObj = pattern.search(value)
        if searchObj:
            return {"departmentstore_distict": searchObj.group()}
        elif len(value) > 1:
            return {"departmentstore_distict": value}
        else:
            dispatcher.utter_message(template="utter_wrong_location")
            return {"departmentstore_distict": None}

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        dispatcher.utter_message(text='flow_departmentstore_' + tracker.get_slot("departmentstore_distict"))
        return [SlotSet("departmentstore_distict")]
        
        
