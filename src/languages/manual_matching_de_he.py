""" Usage:
    <file-name> --in=IN_FILE --out=OUT_FILE [--debug]
"""
# External imports
import logging
import pdb
from docopt import docopt
from collections import Counter
import re
import json

# Local imports
from languages.util import GENDER, get_gender_from_token
from languages.german import GermanPredictor
from languages.semitic_languages import HebrewPredictor
#=-----

class ManualPredictor:
    """
    Class for Manual matching German and Herbrew
    """

    de_variants_fn = "./languages/de_variants.json"
    he_variants_fn = "./languages/he_variants.json"
    
    
    def __init__(self, lang):
        self.lang = lang
        self.automatic_predictor = None
        if self.lang == 'de':
            self.automatic_predictor = GermanPredictor()
            with open(self.de_variants_fn, 'r') as var_json:
                self.variants = json.load(var_json)
        elif self.lang == 'he':
            self.automatic_predictor = HebrewPredictor()
            with open(self.he_variants_fn, 'r') as var_json:
                self.variants = json.load(var_json)
        else:
            raise ValueError(f"Unrecognized language {self.lang}, supported: de and he")
        
        
    def get_gender(self, profession: str, translated_sent = None, entity_index = None, ds_entry = None) -> (GENDER, str):
        """
        Predict gender of an input profession.
        """
        correct_prof = ds_entry[3].lower()
        if ds_entry[0] == "neutral":
            return GENDER.ignore, None

        gender, matched_word = self._get_gender(profession, translated_sent, entity_index, ds_entry)

        return gender, matched_word

    def _get_gender(self, profession: str, translated_sent = None, entity_index = None, ds_entry = None) -> (GENDER, str):
        expected_english_profession = ds_entry[3].lower()
        expected_gender = ds_entry[0]

        # initially try to resolve problem based on exact manual rules
        gender, matched_word = self._get_gender_manual_rules(profession, translated_sent, entity_index, ds_entry)

        if gender in [GENDER.male, GENDER.female, GENDER.neutral]:
            return gender, matched_word

        return self.automatic_predictor.get_gender(profession, translated_sent, entity_index, ds_entry), None

    def _get_gender_manual_rules(self, profession: str, translated_sent = None, entity_index = None, ds_entry = None) -> (GENDER, str):
        expected_english_profession = ds_entry[3].lower()
        expected_gender = ds_entry[0]

        translated_sent = translated_sent.lower()

        found_gender = GENDER.unknown

        male = expected_english_profession + "-male"
        female = expected_english_profession + "-female"
        
        both_possible = False
        matched_word = None
        if male in self.variants:
            for form in self.variants[male]:
                if re.search(form.lower() + "[^a-z\u0590-\u05fe]", translated_sent):
                    found_gender = GENDER.male
                    matched_word = form
                    break
    
        if female in self.variants:
            for form in self.variants[female]:
                if re.search(form.lower() + "[^a-z\u0590-\u05fe]", translated_sent):
                    if found_gender is GENDER.male:
                        found_gender = GENDER.unknown
                        both_possible = True
                        if matched_word != form:
                            matched_word = None
                        break
                    matched_word = form
                    found_gender = GENDER.female

        # our morphology analysis cannot analyze whole sentence, therefore if both are possible, mark it as correct
        if both_possible:
            if expected_gender == "male":
                return GENDER.male, matched_word
            else:
                return GENDER.female, matched_word

        return found_gender, matched_word


if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    inp_fn = args["--in"]
    out_fn = args["--out"]
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    logging.info("DONE")
