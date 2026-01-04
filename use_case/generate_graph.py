"""
# ---------------------------------------------------------------------------- #
#                             GRAPH CREATION SCRIPT                            #
# ---------------------------------------------------------------------------- #

This script uses web scraping to generate a knowledge graph for research
purposes only.

At the end of the script the graph is exported to the configured import volume.
If a file with the name `graph.xml` is already in that volume it will attempt
to import the file instead and refrain from the scraping procedure.
"""

import os
import sys
import time
import tqdm
from dotenv import load_dotenv
from graphs.GraphNeo4j import GraphNeo4j
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


if __name__ == "__main__":
    # ---------------------------------------------------------------------------- #
    #                                     SETUP                                    #
    # ---------------------------------------------------------------------------- #
    load_dotenv()
    GRAPH_IMPORT_VOLUME = os.getenv("NEO4J_IMPORT_VOLUME")
    GRAPH_FILE = "graph.xml"
    BASE_URL = "https://www.langenachtderwissenschaften.de/programm"
    TMP_FILE = "./use_case/event_urls.tmp"
    graph = GraphNeo4j()

    # Import if possible
    try:
        if os.path.exists(f"{GRAPH_IMPORT_VOLUME}/{GRAPH_FILE}"):
            graph.import_graphml(GRAPH_FILE)
            print("Graph imported.")
            graph.close()
            sys.exit(0)
    except Exception as e:
        graph.close()
        sys.exit(f"Something went wrong while importing: {e}")

    driver = webdriver.Chrome(options=Options())

    # ---------------------------------------------------------------------------- #
    #                               INITIAL CREATION                               #
    # ---------------------------------------------------------------------------- #
    # Quellen:
    # https://www.langenachtderwissenschaften.de/fileadmin/media/Pressemitteilungen-2025/03_LNDW_2025_Pressemitteilung_Programmveroeffentlichung.pdf
    # https://www.langenachtderwissenschaften.de/informationen/das-event
    (
        core,
        abbr,
        lndw_descr,
        lndw_organizer,
        date,
        duration,
        anniversary,
        num_facilities,
        website,
        programm_page,
        age_suitable,
        num_events,
        entry_fee,
        media_contact_person,
        berlin,
        type_place,
        type_address,
        type_facility,
        type_event,
        type_category,
        type_time,
        type_number,
        type_url,
        type_organizer,
        type_description,
        type_person,
    ) = graph.create(
        [
            "Lange Nacht der Wissenschaften 2025",
            "LNDW",
            "Die Lange Nacht der Wissenschaften in Berlin ist ein Gemeinschaftsprojekt wissenschaftlicher sowie wissenschaftsnaher Einrichtungen der Region und findet einmal jährlich statt. Veranstalter ist der Lange Nacht der Wissenschaften e. V. (LNDW e. V.), in dem sich wissenschaftliche Einrichtungen zusammengeschlossen haben. Finanziert wird die Lange Nacht der Wissenschaften weitgehend von den beteiligten wissenschaftlichen Einrichtungen selbst. Auch die Ticketeinnahmen werden vollständig für die Finanzierung der Gesamtveranstaltung verwendet. Die Lange Nacht der Wissenschaften wird von zahlreichen Partnern aus der Region unterstützt. Über den Einsatz der Mittel entscheidet die Mitgliederversammlung des LNDW e. V.",
            "Lange Nacht der Wissenschaften e. V. (LNDW e. V.)",
            "Samstag, der 28.Juni 2025",
            "17:00-00:00 Uhr",
            "25",  # Jubiläum
            "etwa 50",  # Anzahl Einrichtungen in Berlin
            "https://www.langenachtderwissenschaften.de",
            "https://www.langenachtderwissenschaften.de/programm",
            "jedes Alter",
            "über 1.000",  # Anzahl Programmpunkte
            "5 Euro",
            "Juri Mertens",
            "Berlin",
            "Ort",  # starting from here: types
            "Adresse",
            "Wissenschaftliche Einrichtung",
            "Veranstaltung",
            "Kategorie",
            "Zeit",
            "Zahl",
            "URL",
            "Veranstalter",
            "Beschreibung",
            "Person",
        ]
    )
    graph.link(
        [
            (core.uuid, "IST_TYP", type_event.uuid),
            (abbr.uuid, "IST_ABKUERZUNG_FUER", core.uuid),
            (date.uuid, "IST_TYP", type_time.uuid),
            (core.uuid, "FINDET_STATT_AM", date.uuid),
            (lndw_descr.uuid, "IST_TYP", type_description.uuid),
            (lndw_descr.uuid, "BESCHREIBT", core.uuid),
            (lndw_organizer.uuid, "IST_TYP", type_organizer.uuid),
            (lndw_organizer.uuid, "ORGANISIERT", core.uuid),
            (duration.uuid, "IST_TYP", type_time.uuid),
            (core.uuid, "FINDET_STATT_VON_BIS", duration.uuid),
            (berlin.uuid, "IST_TYP", type_place.uuid),
            (core.uuid, "FINDET_STATT_IN", berlin.uuid),
            (anniversary.uuid, "IST_TYP", type_number.uuid),
            (core.uuid, "IST_JUBILAEUM", anniversary.uuid),
            (num_facilities.uuid, "IST_TYP", type_number.uuid),
            (core.uuid, "HAT_ANZAHL_TEILNEHMENDER_EINRICHTUNGEN", num_facilities.uuid),
            (website.uuid, "IST_TYP", type_url.uuid),
            (core.uuid, "HAT_WEBSITE", website.uuid),
            (programm_page.uuid, "IST_TYP", type_url.uuid),
            (core.uuid, "HAT_PROGRAMM_ZU_FINDEN_AUF", programm_page.uuid),
            (core.uuid, "IST_GEEIGNET_FUER", age_suitable.uuid),
            (num_events.uuid, "IST_TYP", type_number.uuid),
            (core.uuid, "HAT_ANZAHL_VERANSTALTUNGEN", num_events.uuid),
            (core.uuid, "HAT_EINTRITTSPREIS", entry_fee.uuid),
            (media_contact_person.uuid, "IST_TYP", type_person.uuid),
            (core.uuid, "HAT_KONTAKT_PERSON_FUER_MEDIEN", media_contact_person.uuid),
        ]
    )

    try:
        driver.get(BASE_URL)

        # ---------------------------------------------------------------------------- #
        #                               COOKIE BYPASSING                               #
        # ---------------------------------------------------------------------------- #
        cookie_popup = driver.find_element(By.ID, "bb-cm-notice-necessary")
        if cookie_popup:
            cookie_popup.click()

        # ---------------------------------------------------------------------------- #
        #                              FILTER INTERACTION                              #
        # ---------------------------------------------------------------------------- #
        print("Filtering for TU Berlin")
        filter_btn = driver.find_element(By.LINK_TEXT, "Einrichtungen")
        filter_btn.click()
        dropdown = filter_btn.find_element(By.XPATH, "following-sibling::*[1]")
        time.sleep(1)
        tub_item = dropdown.find_element(By.ID, "attendees20")
        driver.execute_script("arguments[0].click();", tub_item)
        dropdown.find_element(By.CLASS_NAME, "btn-prime").click()
        time.sleep(1)

        # ---------------------------------------------------------------------------- #
        #                                URL COLLECTION                                #
        # ---------------------------------------------------------------------------- #
        detail_page_urls = []
        if os.path.exists(TMP_FILE):
            with open(TMP_FILE, "r") as file:
                print("Found url file. Delete to scrape urls from scratch.")
                content = file.read()
                detail_page_urls = content.split("\n")
        else:
            print("Iterating through pages to collect detail page urls")
            has_next_page = True
            while has_next_page:
                event_elements = driver.find_elements(
                    By.CSS_SELECTOR, "a[href*='/programm/detail']"
                )
                detail_page_urls.extend(
                    [event_elem.get_attribute("href") for event_elem in event_elements]
                )
                try:
                    driver.find_element(By.CLASS_NAME, "next").click()
                    time.sleep(1)
                except:
                    has_next_page = False
            with open(TMP_FILE, "w") as file:
                file.write("\n".join(detail_page_urls))

        print("Generating entities and relationships for each detail page")
        for url in tqdm.tqdm(detail_page_urls):
            driver.get(url)

            page = driver.find_element(By.CLASS_NAME, "veranstaltung-inhaltsseite")
            event_data_blocks = page.find_elements(
                By.CLASS_NAME, "veranstaltung-wrapper"
            )
            event_block = event_data_blocks[0]
            facility_block = event_data_blocks[1]

            # ---------------------------------------------------------------------------- #
            #                                ALWAYS PRESENT                                #
            # ---------------------------------------------------------------------------- #
            title_elem = event_block.find_element(By.TAG_NAME, "h1")
            title = title_elem.get_attribute("innerHTML")

            event_desc = title_elem.find_element(
                By.XPATH, "following-sibling::*[1]"
            ).get_attribute("innerText")

            event_duration = (
                event_block.find_element(By.CLASS_NAME, "veranstaltung-time")
                .get_attribute("innerText")
                .strip()
            )

            facility_elem = facility_block.find_element(By.TAG_NAME, "h2")
            facility_name = facility_elem.get_attribute("innerText")

            facility_description = facility_elem.find_element(
                By.XPATH, "following-sibling::*[1]"
            ).get_attribute("innerText")

            driver.execute_script(
                "window.copyStringToClipboard = (link) => window.capturedLink = link"
            )
            event_block.find_element(By.ID, "copylinkbutton").click()
            event_link = driver.execute_script("return window.capturedLink")

            (
                event_entity,
                duration_entity,
                facility_entity,
                facility_descr_entity,
                event_link_entity,
                event_desc_entity,
            ) = graph.create(
                [
                    title,
                    event_duration,
                    facility_name,
                    facility_description,
                    event_link,
                    event_desc,
                ]
            )
            graph.link(
                [
                    (facility_entity.uuid, "IST_TYP", type_facility.uuid),
                    (facility_entity.uuid, "IST_EINRICHTUNG_IN", berlin.uuid),
                    (event_entity.uuid, "IST_TYP", type_event.uuid),
                    (facility_entity.uuid, "VERANSTALTET", event_entity.uuid),
                    (facility_entity.uuid, "NIMMT_TEIL_AN", core.uuid),
                    (facility_descr_entity.uuid, "IST_TYP", type_description.uuid),
                    (facility_descr_entity.uuid, "BESCHREIBT", facility_entity.uuid),
                    (event_desc_entity.uuid, "IST_TYP", type_description.uuid),
                    (event_desc_entity.uuid, "BESCHREIBT", event_entity.uuid),
                    (event_entity.uuid, "GEHOERT_ZU", core.uuid),
                    (core.uuid, "BEINHALTET", event_entity.uuid),
                    (duration_entity.uuid, "IST_TYP", type_time.uuid),
                    (event_entity.uuid, "FINDET_STATT_VON_BIS", duration_entity.uuid),
                    (event_link_entity.uuid, "IST_TYP", type_url.uuid),
                    (event_entity.uuid, "HAT_URL", event_link_entity.uuid),
                ]
            )

            # ---------------------------------------------------------------------------- #
            #                                   OPTIONAL                                   #
            # ---------------------------------------------------------------------------- #
            try:
                area = event_block.find_element(By.CLASS_NAME, "tag-ort").get_attribute(
                    "innerHTML"
                )
                area_entity = graph.create([area])[0]
                graph.link(
                    [
                        (area_entity.uuid, "IST_TYP", type_place.uuid),
                        (event_entity.uuid, "FINDET_STATT_IN", area_entity.uuid),
                        (area_entity.uuid, "IST_GEGEND_IN", berlin.uuid),
                    ]
                )
            except NoSuchElementException:
                """"""
            try:
                icons = event_block.find_element(
                    By.CLASS_NAME, "veranstaltung-icon-wrapper"
                ).find_elements(By.CLASS_NAME, "tooltip")
                for icon_elem in icons:
                    icon_descr = icon_elem.get_attribute("innerHTML")
                    relationship = ""
                    if "Rollstuhlzugang" in icon_descr:
                        relationship = "HAT_ZUGANG"
                    elif "Kinder" in icon_descr:
                        relationship = "IST_GEEIGNET_FUER"
                    elif "Late-Night" in icon_descr:
                        relationship = "HAT_RELEVANZ"
                    elif "Englisch" in icon_descr:
                        relationship = "IST_AUF_SPRACHE"
                    elif "Speisen" in icon_descr:
                        relationship = "HAT_VORHANDEN"
                    if relationship:
                        icon_entity = graph.create([icon_descr])[0]
                        graph.link(
                            [(event_entity.uuid, relationship, icon_entity.uuid)]
                        )
            except NoSuchElementException:
                """"""

            try:
                tags = [
                    tag.strip()
                    for tag in title_elem.find_element(
                        By.XPATH, "preceding-sibling::*[1]"
                    )
                    .get_attribute("innerHTML")
                    .split(",")
                ]
                for tag in tags:
                    tag_entity = graph.create([tag])[0]
                    graph.link(
                        [
                            (tag_entity.uuid, "IST_TYP", type_category.uuid),
                            (
                                event_entity.uuid,
                                "IST_VERANSTALTUNGSART",
                                tag_entity.uuid,
                            ),
                        ]
                    )
            except NoSuchElementException:
                """"""

            try:
                times = (
                    event_block.find_element(
                        By.XPATH,
                        "//div[@class='veranstaltung-absatz' and contains(text(), 'Veranstaltungszeiten')]",
                    )
                    .get_attribute("innerText")
                    .split("\n")[1:]
                )
                time_entities = graph.create(times)
                graph.link(
                    [
                        (event_entity.uuid, "HAT_VERANSTALTUNG_UM", time_entity.uuid)
                        for time_entity in time_entities
                    ]
                )
                graph.link(
                    [
                        (time_entity.uuid, "IST_TYP", type_time.uuid)
                        for time_entity in time_entities
                    ]
                )
            except NoSuchElementException:
                """"""

            try:
                address = (
                    facility_block.find_element(By.TAG_NAME, "h4")
                    .find_element(By.XPATH, "following-sibling::*[1]")
                    .get_attribute("innerText")
                )
                address_entity = graph.create([address])[0]
                graph.link(
                    [
                        (address_entity.uuid, "IST_TYP", type_address.uuid),
                        (event_entity.uuid, "FINDET_STATT_IN", address_entity.uuid),
                        (address_entity.uuid, "BEFINDET_SICH_IN", berlin.uuid),
                    ]
                )
            except NoSuchElementException:
                """"""

            time.sleep(1)

        os.remove(TMP_FILE)
        print("Exporting graph to file.")
        meta = graph.export_graphml("graph.xml")[0]
        print(f"Entities: {meta["nodes"]}\nRelationships: {meta["relationships"]}")

    except Exception as e:
        print(e)

    time.sleep(5)
    graph.close()
    driver.quit()
