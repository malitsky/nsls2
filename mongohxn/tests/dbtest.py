
from datetime import datetime
from databroker import Broker

scan_id_begin = 48995 # May 29, 2018
scan_id_end   = 53455 # August 8, 2018

f_datatest = open("dbtest.out", "a+")

# define databrokers

db_new = Broker.named('mdb01-new')
db_1 = Broker.named('ca1-1')

# secondary methods

from math import isnan
def clean_data(t):
    if t[0] == 'event': 
        for k in list(t[1]['data'].keys()):
            v = t[1]['data'][k]
            if type(v) != str:
                if v is None:
                    t[1]['data'][k] = 'None'  
                elif isnan(v):
                    t[1]['data'][k] = 'nan'   
    return t

def check_scanid(scan_id):

    scanid_checks = []
    try: 
        hdr_new = db_new[scan_id]
        scanid_checks.append(True)
    except ValueError:
        scanid_checks.append(False)

    try: 
        hdr_1 = db_1[scan_id]
        scanid_checks.append(True)
    except ValueError:
        scanid_checks.append(False)

    return scanid_checks

def check_one_scan(scanid):

    hdr_new = db_new[scanid]
    hdr_1 = db_1[scanid]

    # run_start, run_stop, event_descriptors, and events

    doc_gen_new = db_new.get_documents(hdr_new, fill=False)
    doc_gen_1 = db_1.get_documents(hdr_1, fill=False)

    ds_check = []
    for x, y in zip(doc_gen_new, doc_gen_1):
        x = clean_data(x)
        y = clean_data(y)
        ds_check.append(x == y)

    # resource collection

    res_uids_new = list(db_new.get_resource_uids(hdr_new))
    res_uids_1 = list(db_1.get_resource_uids(hdr_1))

    res_uids_check = (res_uids_new == res_uids_1)

    res_check = []
    for uid in res_uids_new:
        res_doc_new = db_new.reg.resource_given_uid(uid)
        res_doc_1 = db_1.reg.resource_given_uid(uid)   
        res_check.append(res_doc_new == res_doc_1)

    # datum collection

    datum_docs_new = []
    datum_docs_1 = []
    for res_uid in res_uids_new:
        datum_gen_new = db_new.reg.datum_gen_given_resource(res_uid)
        datum_gen_1 = db_1.reg.datum_gen_given_resource(res_uid)
        for datum_new, datum_1 in zip(datum_gen_new, datum_gen_1):
            datum_new.pop('_id')
            datum_1.pop('_id')
            datum_docs_new.append(datum_new)
            datum_docs_1.append(datum_1)

    datum_docs_new = sorted(datum_docs_new,  key=lambda k: k['datum_id'])
    datum_docs_1 = sorted(datum_docs_1, key=lambda k: k['datum_id'])
    datum_check = [doc_new == doc_1 for doc_new, doc_1 in zip(datum_docs_new, datum_docs_1)]

    return ds_check, res_uids_check, res_check, datum_check


for scan_id in range(scan_id_begin, scan_id_end):

    scanid_checks = check_scanid(scan_id)

    if not all(scanid_checks):
        f_datatest.write("{0}, scan checks: {1} \n".format(scan_id, all(scanid_checks),))
        continue

    t1 = datetime.now()
    ds_check, res_uids_check, res_check, datum_check = check_one_scan(scan_id)
    t2 = datetime.now()

    f_datatest.write("{0}, ds({1}): {2}, res uids: {3}, res({4}): {5}, datum({6}): {7}, time: {8} seconds \n".format(
        scan_id,
        len(ds_check), all(ds_check),
        res_uids_check,
        len(res_check), all(res_check),
        len(datum_check), all(datum_check), (t2 - t1),))

    f_datatest.flush()

f_datatest.close()




