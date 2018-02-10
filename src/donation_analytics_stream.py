# The python script for donation analysis: Insight Data Engineer.
# This is the streaming version which outputs when a line is streaming in.

import numpy as np
from collections import defaultdict
import argparse
import os
import time

print('Hello Insight.')
start_time = time.time()

def valid_date(trans_dt):  
# Should not assume the year field holds any particular value. So the year value should be checked.
    valid = 1
    if not (len(trans_dt) == 8):
        valid = 0
    else:
        if int(trans_dt[4:8]) > 2018 or int(trans_dt[4:8]) < 2013:
            valid = 0
        if int(trans_dt[0:2]) > 12 or int(trans_dt[0:2]) < 1:
            valid = 0
        if int(trans_dt[2:4]) > 31 or int(trans_dt[2:4]) < 1:
            valid = 0
    return valid


def valid_zip(zipcode):
# Check for zip code.
    valid = 1
    if len(zipcode) < 5:
        valid = 0
    return valid


def valid_name(name):
# Check for names.
    valid = 1
    if len(name) < 1:
        valid = 0
    return valid

# CMTE_ID, AMT, OTHER_ID assumed to be easily verified.

def valid_all(donation):  
# Include all checkings.

    valid = 1

    CMTE_ID = donation[0]
    #print(CMTE_ID)
    NAME = donation[7]
    #print(NAME)
    ZIP_CODE = donation[10]
    #print(ZIP_CODE)
    TRANS_DT = donation[13]
    #print(TRANS_DT)
    TRANS_AM = donation[14]
    #print(TRANS_AM)
    OTHER = donation[15]
    #print(OTHER)

    if len(CMTE_ID) == 0:
        valid = 0
    if len(TRANS_AM) == 0 or int(TRANS_AM) < 1:
        valid = 0
    if len(OTHER) > 0:
        valid = 0
    if not valid_date(TRANS_DT):
        valid = 0
    #print(valid_date(TRANS_DT))
    if not valid_zip(ZIP_CODE):
        valid = 0
    #print(valid_zip(ZIP_CODE))
    if not valid_name(NAME):
        valid = 0
    #print(valid_name(NAME))

    #print(valid)
    return valid


def get_first_year(donars_years):

    donars_first = dict()

    for donars in donars_years:
        #print(donars)
        years = donars_years[donars]
        donars_first[donars]= min(years)

    return donars_first

# Determine the first_year for each DONAR
# If the new donation for DONAR is later than his first_year, then treat it as repeat donation.
# output the repeat donor


if __name__ == '__main__':
    
    #NUM = 100000 # Num of lines to test on
    #i = 0

    hash_donars = defaultdict(list)
    hash_donars_years = defaultdict(set)
    # A dict() which contains donations for each DONAR.  defaultdict() for multipy mapping.
    zips = defaultdict(set)
    # A dict() which contains all DONARS for each Zip. 

    parser = argparse.ArgumentParser()
    parser.add_argument('itcont_path',help='itcont.txt path')
    parser.add_argument('percentile_path',help='percentile.txt path')
    parser.add_argument('repeat_donor_path',help='repeat_donor.txt path')
    args = parser.parse_args()
    itcont_path = args.itcont_path
    percentile_path = args.percentile_path
    repeat_donor_path = args.repeat_donor_path

    #itcont_path = '../input/itcont.txt'
    #percentile_path = '../input/percentile.txt'
    #repeat_donor_path = '../output/repeat_donors.txt'

    print('start')

    print('read in percentile.')

    with open(percentile_path) as percentile:
        perc = int(percentile.read())
        print('percentile is: ')
        print(perc)

    if os.path.exists(repeat_donor_path):
        os.remove(repeat_donor_path)

    # Determine the first_year for all DONARS:
    print('read in donations.')
    with open(itcont_path) as f:

        try:
            while True:
                line = next(f)
                donation = line.split('|')

                if valid_all(donation):

                    # Create donation_dict for each line. O(k) for k keys.
                    donation_dict = dict()
                    donation_dict['CMTE_ID'] = donation[0]
                    #donation_dict['NAME'] = donation[7]
                    donation_dict['ZIP_CODE'] = donation[10][0:5]
                    donation_dict['DONAR'] = donation[7] + '_' + donation[10][0:5]
                    #donation_dict['TRANS_DT'] = donation[13]
                    donation_dict['YEAR'] = donation[13][4:8]
                    donation_dict['TRANS_AM'] = int(donation[14])

                    # append for each donation_dict. O(n) for n lines.
                    hash_donars[donation_dict['DONAR']].append(donation_dict)
                    hash_donars_years[donation_dict['DONAR']].add(int(donation_dict['YEAR']))
                    zips[donation_dict['ZIP_CODE']].add(donation[7] + '_' + donation[10][0:5])
                    #print(line)

                    # In total, (O(k)+O(1)) for n lines. So O(nk), k is constant thus O(n).

        except StopIteration:
            pass

    #print(hash_donars_years)
    #print(hash_donars)
    #print(zips)

    # Get another hash with first_year for each DONAR
    hash_donars_first = dict()
    hash_donars_first = get_first_year(hash_donars_years)

    hash_zips_count = dict()
    hash_zips_amount = dict()

    for zip_id in zips:
        hash_zips_count[zip_id] = 0
        hash_zips_amount[zip_id] = 0

    hash_zips_amounts = defaultdict(list)
    # Start loop over all donations and determine all:
    Ntotal = len(hash_donars)
    i = 0

    print('start extract and output')
    with open(repeat_donor_path,'a') as out:
        for donars in hash_donars:
            # for each DONAR, get donations.
            i += 1

            if i % 1000 == 0: 
            	print('donar:'+str(i)+'/'+str(Ntotal))
            
            #print(donars)
            donations = hash_donars[donars] # Now it is a list
            donations_years = hash_donars_years[donars] # It is a set
            first = hash_donars_first[donars]

            if len(donations_years)>1:
                for donors in donations:
                    if int(donors['YEAR']) > first:
                        hash_zips_count[donors['ZIP_CODE']] += 1
                        hash_zips_amount[donors['ZIP_CODE']] += donors['TRANS_AM']
                        hash_zips_amounts[(donors['ZIP_CODE'],donors['YEAR'])].append(donors['TRANS_AM'])

                        perc_value = int(round(np.percentile(hash_zips_amounts[(donors['ZIP_CODE'],donors['YEAR'])],perc,interpolation='lower'),0))

                        amount = hash_zips_amount[donors['ZIP_CODE']]
                        num = hash_zips_count[donors['ZIP_CODE']]

                        repeat_donor = '|'.join([donors['CMTE_ID'], donors['ZIP_CODE'], donors['YEAR'], str(perc_value), str(amount), str(num)])

                        #print(repeat_donor)
                        out.write(repeat_donor)
                        out.write('\n')

    print('Done.')
    print('%s seconds',time.time()-start_time)



