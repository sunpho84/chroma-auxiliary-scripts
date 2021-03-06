#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright © 2016-2017 Martin Ueding <dev@martin-ueding.de>

import collections
import glob
import os

from lxml import etree
import numpy as np

import extractors
import names
import transforms


parser = etree.XMLParser(recover=False)


def main(options):
    for dirname in options.dirname:
        try:
            process_directory(dirname)
        except FileNotFoundError as e:
            print(e)


def process_directory(dirname):
    extractors.print_progress(dirname)
    for key, extractor in bits.items():
        extracted = extractor(dirname)
        if extracted is not None:
            extracted = list(extracted)
            if len(extracted) != 0:
                update_no_list, number_list = extracted
                outfile = os.path.join(dirname, 'extract-{}.tsv'.format(key))
                np.savetxt(outfile, np.column_stack([update_no_list, number_list]))

    transforms.convert_tau0_to_md_time(dirname)
    transforms.convert_time_to_minutes(dirname)

    for name in ['w_plaq', 'deltaH', 'n_steps']:
        transforms.convert_to_md_time(dirname, name)


def extractor_to_shard(extractor, xml_file, key):
    extracted = extractor(xml_file)
    update_no_list, number_list = extracted
    outfile = names.xpath_shard(xml_file, key)
    np.savetxt(outfile, np.column_stack([update_no_list, number_list]))


def make_xpath_extractor(xpath, transform=float):
    def extractor(xml_file):
        return extract_xpath_from_all(xml_file, xpath, transform)
    return extractor


def make_single_xpath_extractor(xpath, transform=float):
    def extractor(xml_file):
        update_no_list = []
        number_list = []

        step_sizes = {}

        try:
            tree = etree.parse(xml_file, parser)
        except etree.XMLSyntaxError as e:
            print('XML file could not be loaded')
            print(e)
        else:
            if len(tree.xpath('//doHMC')) >= 0:
                number = transform(tree.xpath(xpath)[0])

                updates = tree.xpath('//Update')

                for update in updates:
                    update_no = int(update.xpath('./update_no/text()')[0])

                    if update_no in update_no_list:
                        # This number is already extracted for that update. Make
                        # sure that the extracted value is the same.
                        index = update_no_list.index(update_no)
                        assert number_list[index] == number
                    else:
                        update_no_list.append(update_no)
                        number_list.append(number)

        if len(update_no_list) == 0:
            return [], []
        else:
            return list(zip(*sorted(zip(update_no_list, number_list))))

    return extractor


def extract_xpath_from_all(xml_file, xpath, transform=float):
    update_no_list = []
    number_list = []

    try:
        tree = etree.parse(xml_file, parser)
    except etree.XMLSyntaxError as e:
        print('XML file could not be loaded')
        print(e)
    else:
        updates = tree.xpath('//Update')

        for update in updates:
            update_no = int(update.xpath('./update_no/text()')[0])

            number_list_local = []

            matches = update.xpath(xpath)
            if len(matches) == 0:
                print("No measurements of {} in XML file {}".format(xpath, xml_file))
                continue

            number = transform(matches[0])

            if update_no in update_no_list:
                # This number is already extracted for that update. Make sure
                # that the extracted value is the same.
                index = update_no_list.index(update_no)
                assert number_list[index] == number
            else:
                update_no_list.append(update_no)
                number_list.append(number)

    if len(update_no_list) == 0:
        return [], []

    update_no_list, number_list = zip(*sorted(zip(update_no_list, number_list)))

    return update_no_list, number_list


bits = {
    'w_plaq': make_xpath_extractor('.//w_plaq/text()'),
    'deltaH': make_xpath_extractor('.//deltaH/text()'),
    'DeltaDeltaH': make_xpath_extractor('.//DeltaDeltaH/text()'),
    'seconds_for_trajectory': make_xpath_extractor('.//seconds_for_trajectory/text()'),
    'tau0': make_single_xpath_extractor('//hmc/Input/Params/HMCTrj/MDIntegrator/tau0/text()'),
    'n_steps': make_single_xpath_extractor('//hmc/Input/Params/HMCTrj/MDIntegrator/Integrator/n_steps/text()'),
    'AcceptP': make_xpath_extractor('.//AcceptP/text()', lambda x: x == 'true'),
}
