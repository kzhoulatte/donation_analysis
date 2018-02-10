# The python script for donation analysis: Insight Data Engineer.

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


# CMTE_ID, AMT, OTHER_ID can be easily verified.

def valid_all(donation):  
# Include all checkings.

    valid = 1

    CMTE_ID = donation[0]
    NAME = donation[7]
    ZIP_CODE = donation[10]
    TRANS_DT = donation[13]
    TRANS_AM = donation[14]
    OTHER = donation[15]

    if len(CMTE_ID) == 0:
        valid = 0
    if len(TRANS_AM) == 0 or int(TRANS_AM) < 1:
        valid = 0
    if len(OTHER) > 0:
        valid = 0
    if not valid_date(TRANS_DT):
        valid = 0
    if not valid_zip(ZIP_CODE):
        valid = 0
    if not valid_name(NAME):
        valid = 0
  
    return valid

def order_time(donors_var):
# Delete the donors in first year and return all the repeat donors in a list.
    donors_ordered = []
    years = set()
    #print(donors_var)
    for donor_var in donors_var:
        years.add(int(donor_var['YEAR']))

    year_first = min(years)

    for donor_var in donors_var:
        if int(donor_var['YEAR']) > year_first:
            donors_ordered.append(donor_var)

    return donors_ordered

if __name__ == '__main__':
    
    #NUM = 100000 # Num of lines to test on
    #i = 0

    hash_donars = defaultdict(list)
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

    print('start read in')

    with open(itcont_path) as f:

        try:
            while True:
                line = next(f)
                #i += 1
                donation = line.split('|')

                if valid_all(donation):

                    # Create donation_dict for each line. O(k) for k keys. 

                    donation_dict = dict()
                    donation_dict['CMTE_ID'] = donation[0]
                    donation_dict['NAME'] = donation[7]
                    donation_dict['ZIP_CODE'] = donation[10][0:5]
                    donation_dict['DONAR'] = donation[7] + '_' + donation[10][0:5]
                    donation_dict['TRANS_DT'] = donation[13]
                    donation_dict['YEAR'] = donation[13][4:8]
                    donation_dict['TRANS_AM'] = donation[14]
                    # append for each donation_dict. O(n) for n lines. 
                    hash_donars[donation_dict['DONAR']].append(donation_dict)
                    zips[donation_dict['ZIP_CODE']].add(donation[7] + '_' + donation[10][0:5])
                    # In total, (O(k)+O(1)) for n lines. So O(nk), k is constant thus O(n).

        except StopIteration:
            pass

    #print(hash_donars)
    #print(hash_zips)
    #print(zips)

    print('read in percentile.')
    print('percentile is: ')
    with open(percentile_path) as percentile:
        perc = int(percentile.read())
        print(perc)

    if os.path.exists(repeat_donor_path):
        os.remove(repeat_donor_path)

    print('start output repeat donors.')

    with open(repeat_donor_path, 'a') as out:

        # Zip - Donars - Donors
        zip_len = len(zips)
        print(zip_len)
        zip_num = 0
        for zip_id in zips: 
        # For each zip code, get the DONARS and calculate repeat donors. 
        # O(z) for z zip codes.
            amounts_total = defaultdict(list) # For each zip code and each year.
            zip_num += 1
            print('zip:'+str(zip_num)+'/'+str(zip_len))

            i = 0
            amount = 0
            donars_zip= zips[zip_id]
            # O(1) for dict() hash search. 

            for donars in donars_zip:
            # For each DONARS inside each zip code.
            # O(d) for d_i DONARS each zip code. 

                if 1<len(hash_donars[donars]):
                    donors_ordered_last = order_time(hash_donars[donars])
                    # Delete the donors in first year. Return all other donors.
             
                    if len(donors_ordered_last)>0:
                        for donors in donors_ordered_last:
                        # For each repeat donor inside each donars.
                        # O(d_2) for d_2i DONORS after first year.
                            i += 1
                            amount += int(donors['TRANS_AM'])
                            #print(amount)
                            amounts_total[donors['YEAR']].append(int(donors['TRANS_AM']))
                            #print(amounts_total)
                            #amounts_total.append(amount)
                            perc_value = int(round(np.percentile(amounts_total[donors['YEAR']],perc,interpolation='lower'),0))

                            repeat_donor = '|'.join([donors['CMTE_ID'],donors['ZIP_CODE'],donors['YEAR'],str(perc_value),str(amount),str(i)])

                            #print(repeat_donor)
                            out.write(repeat_donor)
                            out.write('\n')

                            # For this part, O(z*d_i*d_2i). Approximately O(nd_2i) which depends on how d_i distributes.

    print('Done.')
    print('%s seconds', time.time() - start_time)



