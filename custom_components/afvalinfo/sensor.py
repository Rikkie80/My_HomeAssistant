#!/usr/bin/env python3
"""
Sensor component for Afvalinfo
Author: Johnny Visser

ToDo: Add huisnummer toevoeging
ToDo: Fix all the next year problems
ToDo: Add the following gemeenten:
PDF: #####################################################################################################
Bergen Limburg                  bergen.nl/home/afval_44490/item/afvalkalender-2020_38953.html (PDF)
Dantumadeel                     https://www.dantumadiel.frl/afvalkalender Woont u in het voormalige Ferwerderadiel dan wordt het afval opgehaald door Omrin (PDF)
Delfzijl                        https://www.delfzijl.nl/inwoners/afvalkalender_43586/ (PDF)
Edam-Volendam                   https://www.edam-volendam.nl/portal-home/inzamelkalender_43466/ (PDF)
Eemnes                          https://www.eemnes.nl/inwoners/Afval/Afvalwijzer (PDF)
Gennep                          https://www.gennep.nl/document.php?m=28&fileid=98242&f=834a3177a76c30293e3e9d1c200729fb&attachment=0&c=34148 (PDF)
Goes                            https://afvalkalender.goes.nl/4461AB-2.html (PDF)
Hellevoetsluis                  https://www.hellevoetsluis.nl/Inwoners/WONEN_EN_LEEFOMGEVING/Afval/Afvalkalender (PDF)
Landerd                         https://www.landerd.nl/inwoners-en-ondernemers/afval/afvalkalender/pdf/2020 (PDF)
Landsmeer                       https://admin.sduconnect.nl/linked_links/1577977473Afvalkalender_2020_DEF.pdf (PDF)
Middelburg                      https://www.middelburg.nl/Inwoners/Afval/Ophaaldagen_huisvuil (PDF)
Mook en Middelaar               https://www.mookenmiddelaar.nl/inwoner/afval-en-duurzaamheid_42542/item/afvalkalender-2020_40888.html (PDF)
Oegstgeest                      https://www.oegstgeest.nl/fileadmin/editor/Documenten/Inwoners/Alles_over_afval/afvalkalender_2020_v8.pdf (PDF)
Oostzaan                        https://www.oostzaan.nl/mozard/document/docnr/1182761/bijlage%20-%20afvalkalender%20Oostzaan%202020%20-%20met%20wijkindeling (PDF)
Ouder-Amstel                    https://www.ouder-amstel.nl/Home/Nieuws_en_actualiteiten/Nieuws/Alle_nieuwsberichten_2020/April/Data_inzameling_afval (PDF)
Reusel-De Mierden               https://www.reuseldemierden.nl/document.php?m=25&fileid=123208&f=3e3d90c015a9b15ffc98c993c8e4e9da&attachment=0&c=40975 (PDF)
Rozendaal                       https://www.rozendaal.nl/dsresource?objectid=d7a004f0-ff97-490a-8837-1b66e5bc11e1&type=org (PDF)
Uithoorn                        https://www.uithoorn.nl/Home/Afval/Afvalkalender (PDF)
Vlissingen                      https://www.vlissingen.nl/inwoner/afval-en-milieu/afval/huishoudelijk-afval-en-afvalkalender.html (PDF)
Zundert                         https://www.zundert.nl/afval-en-milieustraat/afvalkalender-2020.html (PDF)
Steenbergen                     https://www.gemeente-steenbergen.nl/inwoners_overzicht/afval/ (PDF)
Vlieland                        https://www.vlieland.nl/v-zelf-regelen/producten_42533/product/afval-huishoudelijk-afval_17.html (PDF)
#############################################################################################################
Buurt / dorp indeling of geen kalender: #####################################################################
Weert                           https://www.weert.nl/huisvuil-duobak-en-ophaaldagen
Texel                           https://www.texel.nl/mozard/!suite86.scherm0325?mVrg=5059
Maassluis                       https://www.maassluis.nl/wonen-verkeer-en-veiligheid/afvalinzameling_43871/
Voorschoten                     https://www.voorschotenmaakthetverschil.nl/ 2251dn 121
Nederweert                      https://www.nederweert.nl/inwoners/huisvuil-2019_45554/
Amsterdam                       Geen kalender, alleen inleverpunten
Schiermonnikoog                 Geen kalender
############################################################################################################
############################################################################################################
"""

import voluptuous as vol
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import urllib.error
from babel import Locale
from babel.dates import format_date, format_datetime, format_time
import re

from .const.const import (
    MIN_TIME_BETWEEN_UPDATES,
    _LOGGER,
    CONF_CITY,
    CONF_LOCATION,
    CONF_POSTCODE,
    CONF_STREET_NUMBER,
    CONF_DATE_FORMAT,
    CONF_TIMESPAN_IN_DAYS,
    CONF_LOCALE,
    CONF_ID,
    SENSOR_PREFIX,
    ATTR_LAST_UPDATE,
    ATTR_HIDDEN,
    ATTR_DAYS_UNTIL_COLLECTION_DATE,
    ATTR_IS_COLLECTION_DATE_TODAY,
    ATTR_YEAR_MONTH_DAY_DATE,
    SENSOR_TYPES,
)

from .location.hoekschewaard import HoekscheWaardAfval
from .location.katwijk import KatwijkAfval
from .location.middendrenthe import MiddenDrentheAfval
from .location.trashapi import TrashApiAfval
from .location.uden import UdenAfval
from .location.veldhoven import VeldhovenAfval
from .location.venlo import VenloAfval
from .location.westerwolde import WesterwoldeAfval
from .location.westland import WestlandAfval

from .sensortomorrow import AfvalInfoTomorrowSensor
from .sensortoday import AfvalInfoTodaySensor

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_RESOURCES
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_RESOURCES, default=[]): vol.All(
            cv.ensure_list, [vol.In(SENSOR_TYPES)]
        ),
        vol.Optional(CONF_CITY, default=""): cv.string,
        vol.Optional(CONF_LOCATION, default="sliedrecht"): cv.string,
        vol.Required(CONF_POSTCODE, default="3361AB"): cv.string,
        vol.Required(CONF_STREET_NUMBER, default="1"): cv.string,
        vol.Optional(CONF_DATE_FORMAT, default = "%d-%m-%Y"): cv.string,
        vol.Optional(CONF_TIMESPAN_IN_DAYS, default="365"): cv.string,
        vol.Optional(CONF_LOCALE, default = "en"): cv.string,
        vol.Optional(CONF_ID, default = ""): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    _LOGGER.debug("Setup Afvalinfo sensor")

    location = config.get(CONF_CITY).lower().strip()
    if len(location) == 0:
        location = config.get(CONF_LOCATION).lower().strip()
    postcode = config.get(CONF_POSTCODE).strip()
    street_number = config.get(CONF_STREET_NUMBER)
    date_format = config.get(CONF_DATE_FORMAT).strip()
    timespan_in_days = config.get(CONF_TIMESPAN_IN_DAYS)
    locale = config.get(CONF_LOCALE)
    id_name = config.get(CONF_ID)

    try:
        resourcesMinusTodayAndTomorrow = config[CONF_RESOURCES].copy()
        if "trash_type_today" in resourcesMinusTodayAndTomorrow:
            resourcesMinusTodayAndTomorrow.remove("trash_type_today")
        if "trash_type_tomorrow" in resourcesMinusTodayAndTomorrow:
            resourcesMinusTodayAndTomorrow.remove("trash_type_tomorrow")

        data = AfvalinfoData(location, postcode, street_number, resourcesMinusTodayAndTomorrow)
    except urllib.error.HTTPError as error:
        _LOGGER.error(error.reason)
        return False

    entities = []

    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()

        #if sensor_type not in SENSOR_TYPES:
        if sensor_type.title().lower() != "trash_type_today" and sensor_type.title().lower() != "trash_type_tomorrow":
            entities.append(AfvalinfoSensor(data, sensor_type, date_format, timespan_in_days, locale, id_name))

        #Add sensor -trash_type_today
        if sensor_type.title().lower() == "trash_type_today":
            today = AfvalInfoTodaySensor(data, sensor_type, entities, id_name)
            entities.append(today)
        #Add sensor -trash_type_tomorrow
        if sensor_type.title().lower() == "trash_type_tomorrow":
            tomorrow = AfvalInfoTomorrowSensor(data, sensor_type, entities, id_name)
            entities.append(tomorrow)

    add_entities(entities)


class AfvalinfoData(object):
    def __init__(self, location, postcode, street_number, resources):
        self.data = None
        self.location = location
        self.postcode = postcode
        self.street_number = street_number
        self.resources = resources

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        _LOGGER.debug("Updating Waste collection dates")
        hoekschewaard = ["hoeksche waard"]
        if self.location in hoekschewaard:
            self.data = HoekscheWaardAfval().get_data(
                self.location, self.postcode, self.street_number, self.resources
            )
        katwijk = ["katwijk"]
        if self.location in katwijk:
            self.data = KatwijkAfval().get_data(
                self.location, self.postcode, self.street_number, self.resources
            )
        middendrenthe = ["midden-drenthe"]
        if self.location in middendrenthe:
            self.data = MiddenDrentheAfval().get_data(
                self.location, self.postcode, self.street_number, self.resources
            )
        trashapi = ["aa en hunze", "aalsmeer", "aalten", "achtkarspelen", "alblasserdam", "albrandswaard", "alkmaar", "almelo", "almere", "alphen aan den rijn", "alphen-chaam", "altena", "ameland", "amersfoort", "amstelveen", "apeldoorn", "appingedam", "arnhem", "assen", "asten", "baarle-nassau", "baarn", "barendrecht", "barneveld", "beek", "beekdaelen", "beemster", "beesel", "berg en dal", "bergeijk", "bergen op zoom", "bergen", "berkelland", "bernheze", "best", "beuningen", "beverwijk", "bladel", "blaricum", "bloemendaal", "bodegraven-reeuwijk", "boekel", "borger-odoorn", "borne", "borsele", "boxmeer", "boxtel", "breda", "brielle", "bronckhorst", "brummen", "brunssum", "bunnik", "bunschoten", "buren", "capelle aan den ijssel", "castricum", "coevorden", "cranendonck", "cuijk", "culemborg", "dalfsen", "dantumadeel f", "de bilt", "de friese meren", "de ronde venen", "de wolden", "delft", "den haag", "den helder", "deurne", "deventer", "diemen", "dinkelland", "doesburg", "doetinchem", "dongen", "dordrecht", "drechterland", "drimmelen", "dronten", "druten", "duiven", "echt-susteren", "ede", "eersel", "eijsden-margraten", "eindhoven", "elburg", "emmen", "enkhuizen", "enschede", "epe", "ermelo", "etten-leur", "geertruidenberg", "geldrop-mierlo", "gemert-bakel", "gilze en rijen", "goeree-overflakkee", "goirle", "gooise meren", "gorinchem", "gouda", "grave", "groningen", "gulpen-wittem", "haaksbergen", "haaren", "haarlem", "haarlemmermeer", "halderberge", "hardenberg", "harderwijk", "hardinxveld-giessendam", "harlingen", "hattem", "heemskerk", "heemstede", "heerde", "heerenveen", "heerhugowaard", "heerlen", "heeze-leende", "heiloo", "hellendoorn", "helmond", "hendrik-ido-ambacht", "hengelo", "het hogeland (bedum, winsum)", "het hogeland (de marne, eemsmond)", "heumen", "heusden", "hillegom", "hilvarenbeek", "hilversum", "hof van twente", "hollands kroon", "hoogeveen", "hoorn", "horst aan de maas", "houten", "huizen", "hulst", "ijsselstein", "kaag en braassem", "kampen", "kapelle", "kerkrade", "koggenland", "krimpen aan den ijssel", "krimpenerwaard", "laarbeek", "landgraaf", "langedijk", "lansingerland", "laren", "leeuwarden", "leiden", "leiderdorp", "leidschendam-voorburg", "lelystad", "leudal", "leusden", "lingewaard", "lisse", "lochem", "loon op zand", "lopik", "loppersum", "losser", "maasdriel", "maasgouw", "maastricht", "medemblik", "meerssen", "meierijstad", "meppel", "midden-delfland", "midden-groningen", "mill en sint hubert", "moerdijk", "molenlanden", "montferland", "montfoort", "mook en middelaar", "neder-betuwe", "nieuwegein", "nieuwkoop", "nijkerk", "nijmegen", "nissewaard", "noardeast fryslan", "noord-beveland", "noordenveld", "noordoostpolder", "noordwijk", "nuenen", "nunspeet", "oirschot", "oisterwijk", "oldambt", "oldebroek", "oldenzaal", "olst-wijhe", "ommen", "oost gelre", "oosterhout", "ooststellingwerf", "opmeer", "opsterland", "oss", "oude ijsselstreek", "oude pekela", "oudewater", "overbetuwe", "papendrecht", "peel en maas", "pijnacker-nootdorp", "purmerend", "putten", "raalte", "reimerswaal", "renkum", "renswoude", "rheden", "rhenen", "ridderkerk", "rijssen-holten", "rijswijk", "roerdalen", "roermond", "roosendaal", "rotterdam rozenburg", "rotterdam", "rucphen", "s-hertogenbosch", "schagen", "scherpenzeel", "schiedam", "schouwen-duiveland", "simpelveld", "sint anthonis", "sint-michielsgestel", "sittard-geleen", "sliedrecht", "sluis", "smallingerland", "soest", "someren", "son en breugel", "stadskanaal", "staphorst", "stede broec", "steenwijkerland", "stein", "stichtse vecht", "terneuzen", "terschelling", "teylingen", "tholen", "tiel", "tietjerksteradeel", "tilburg", "tubbergen", "twenterand", "tynaarlo", "uitgeest", "urk", "utrecht", "utrechtse heuvelrug", "vaals", "valkenburg aan de geul", "valkenswaard", "veendam", "veenendaal", "veere", "velsen", "venray", "vijfheerenlanden", "vlaardingen", "voerendaal", "voorst", "vught", "waadhoeke", "waalre", "waalwijk", "waddinxveen", "wageningen", "wassenaar", "waterland", "weesp", "west betuwe", "west maas en waal", "westerkwartier", "westerveld", "westervoort", "weststellingwerf", "westvoorne", "wierden", "wijchen", "wijdemeren", "wijk bij duurstede", "winterswijk", "woensdrecht", "woerden", "wormerland", "woudenberg", "zaanstad", "zaltbommel", "zandvoort", "zeewolde", "zeist", "zevenaar", "zoetermeer", "zoeterwoude", "zuidplas", "zuidwest-friesland", "zutphen", "zwartewaterland", "zwijndrecht", "zwolle"]
        if self.location in trashapi:
            self.data = TrashApiAfval().get_data(
                self.location, self.postcode, self.street_number, self.resources
            )
        uden = ["uden"]
        if self.location in uden:
            self.data = UdenAfval().get_data(
                self.location, self.postcode, self.street_number, self.resources
            )
        veldhoven = ["veldhoven"]
        if self.location in veldhoven:
            self.data = VeldhovenAfval().get_data(
                self.location, self.postcode, self.street_number, self.resources
            )
        venlo = ["venlo"]
        if self.location in venlo:
            self.data = VenloAfval().get_data(
                self.location, self.postcode, self.street_number, self.resources
            )
        westerwolde = ["westerwolde"]
        if self.location in westerwolde:
            self.data = WesterwoldeAfval().get_data(
                self.location, self.postcode, self.street_number, self.resources
            )
        westland = ["westland"]
        if self.location in westland:
            self.data = WestlandAfval().get_data(
                self.location, self.postcode, self.street_number, self.resources
            )

class AfvalinfoSensor(Entity):
    def __init__(self, data, sensor_type, date_format, timespan_in_days, locale, id_name):
        self.data = data
        self.type = sensor_type
        self.date_format = date_format
        self.timespan_in_days = timespan_in_days
        self.locale = locale
        self._name = SENSOR_PREFIX + (id_name + " " if len(id_name) > 0  else "") + SENSOR_TYPES[sensor_type][0]
        self._icon = SENSOR_TYPES[sensor_type][1]
        self._hidden = False
        self._state = None
        self._last_update = None
        self._days_until_collection_date = None
        self._is_collection_date_today = False
        self._year_month_day_date = None

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def state(self):
        return self._state

    @property
    def device_state_attributes(self):
        return {ATTR_YEAR_MONTH_DAY_DATE: self._year_month_day_date, ATTR_LAST_UPDATE: self._last_update, ATTR_HIDDEN: self._hidden, ATTR_DAYS_UNTIL_COLLECTION_DATE: self._days_until_collection_date, ATTR_IS_COLLECTION_DATE_TODAY: self._is_collection_date_today}

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        self.data.update()
        waste_data = self.data.data

        try:
            if waste_data:
                if self.type in waste_data:
                    collection_date = datetime.strptime(
                        waste_data[self.type], "%Y-%m-%d"
                    ).date()

                    # Date in date format "%Y-%m-%d"
                    self._year_month_day_date = str(collection_date)

                    if collection_date:
                        # Set the values of the sensor
                        self._last_update = datetime.today().strftime("%d-%m-%Y %H:%M")

                        # Is the collection date today?
                        self._is_collection_date_today = date.today() == collection_date

                        # Days until collection date
                        delta = collection_date - date.today()
                        self._days_until_collection_date = delta.days

                        # Only show the value if the date is lesser than or equal to (today + timespan_in_days)
                        if collection_date <= date.today() + relativedelta(days=int(self.timespan_in_days)):
                            #if the date does not contain a named day or month, return the date as normal
                            if (self.date_format.find('a') == -1 and self.date_format.find('A') == -1
                            and self.date_format.find('b') == -1 and self.date_format.find('B') == -1):
                                self._state = collection_date.strftime(self.date_format)
                            #else convert the named values to the locale names
                            else:
                                edited_date_format = self.date_format.replace('%a', 'EEE')
                                edited_date_format = edited_date_format.replace('%A', 'EEEE')
                                edited_date_format = edited_date_format.replace('%b', 'MMM')
                                edited_date_format = edited_date_format.replace('%B', 'MMMM')

                                #half babel, half date string... something like EEEE 04-MMMM-2020
                                half_babel_half_date = collection_date.strftime(edited_date_format)

                                #replace the digits with qquoted digits 01 --> '01'
                                half_babel_half_date = re.sub(r"(\d+)", r"'\1'", half_babel_half_date)
                                #transform the EEE, EEEE etc... to a real locale date, with babel
                                locale_date = format_date(collection_date, half_babel_half_date, locale=self.locale)

                                self._state = locale_date
                        else:
                            self._hidden = True
                    else:
                        raise ValueError()
                else:
                    raise ValueError()
            else:
                raise ValueError()
        except ValueError:
            self._state = None
            self._hidden = True
            self._days_until_collection_date = None
            self._year_month_day_date = None
            self._is_collection_date_today = False
            self._last_update = datetime.today().strftime("%d-%m-%Y %H:%M")
