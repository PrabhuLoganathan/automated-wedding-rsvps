from __future__ import print_function
import pandas as pd
import numpy as np
from df2gspread import df2gspread as d2g
from df2gspread import gspread2df as g2d
import gspread

def clean_jotform(jotform_id):
    """
    Read the Jotform data from a google spreadsheet and returned the cleaned
    pandas DataFrame.

    Parameters
    ----------
    jotform_id : str
        the google sheet ID

    Returns
    -------
    df : DataFrame
        the pandas data frame holding the RSVP submission data
    """
    # read the data
    kws = {'col_names':True, 'row_names':False, 'start_cell':'A1'}
    data = g2d.download(jotform_id, 'Sheet1', **kws)

    # set empty cells to null
    data = data.replace("", np.nan)

    # remove entries where First Name and Last Name are null
    invalid = np.ones(len(data), dtype='?')
    for col in ['First Name', 'Last Name']:
        invalid &= data[col].isnull()
    data = data[~invalid]

    # store submission date as a data and sort by it
    data['Submission Date'] = pd.to_datetime(data['Submission Date'])
    data = data.sort_values(by=['Submission Date'])

    # remove duplicates, keeping last entry (most recent entry)
    data = data.drop_duplicates(subset=['First Name', 'Last Name'], keep='last')

    return data

def get_rsvps(df, YES, NO):
    """
    Parse the cleaned Jotform data and determine the RSVP responses for each
    online submission.

    Parameters
    ----------
    """
    # initialize the return dataframe
    columns = ['Submission Date', 'Name', 'Yes', 'No', 'Special Food Requests?', 'Comments or Questions']
    out = pd.DataFrame(columns=columns)

    cnt = 0
    # loop over each submission
    for i, row in df.iterrows():

        row = row.dropna() # remove null entries
        iyes = row.index[row == YES] # yes?
        ino =  row.index[row == NO] # no?
        submitter = row['First Name'].capitalize() + " " + row['Last Name'].capitalize()

        # check for no yes/no entry on form (automatic YES)
        if not len(iyes) and not len(ino):
            iyes = ['No Label']

        # handle YES
        for name in iyes:

            # handle singles case (submitted yes/no is marked as "No Label")
            if name == 'No Label':
                name = submitter

            # copy the columns we want to output dataframe
            for col in columns:
                if col in row:
                    out.loc[cnt, col] = row[col]
            out.loc[cnt, 'Yes'] = 1
            out.loc[cnt, 'Name'] = name
            cnt += 1

        # handle NO
        for name in ino:

            # handle singles case (submitted yes/no is marked as "No Label")
            if name == 'No Label':
                name = submitter # use submitter name

            # copy the columns we want to output dataframe
            for col in columns:
                if col in row:
                    out.loc[cnt, col] = row[col]
            out.loc[cnt, 'No'] = 1
            out.loc[cnt, 'Name'] = name
            cnt += 1

    # fill NaN
    out = out.fillna(value="")
    return out


def upload(upload_id, df):
    """
    Upload the cleaned data to a google spreadsheet and update the
    RSVP master list with the answers from the RSVP master list.

    Parameters
    ----------
    upload_id : str
        the id of the google spreadsheet we are uploading to; this should have
        a sheet called 'RSVP List' which contains the master RSVP list
    df : DataFrame
        the cleaned online RSVP data, with submission date, name, and response
    """
    # upload to clean data to the sheet labeled "RSVP Submissions"
    kws = {'wks_name':'RSVP Submissions', 'row_names':False, 'clean':True, 'start_cell':'A6'}
    ws = d2g.upload(df, gfile=upload_id, **kws)

    # add a warning to first cell
    ws.update_acell('A1', 'WARNING DO NOT EDIT: THIS IS AUTOMATICALLY GENERATED')

    # compute the totals
    total_yes = (df['Yes']==1).sum()
    total_no  = (df['No']==1).sum()

    # add totals to sheet
    ws.update_acell('B3', 'Yes')
    ws.update_acell('C3', 'No')
    ws.update_acell('A4', 'Totals')
    ws.update_acell('B4', '%d' %total_yes)
    ws.update_acell('C4', '%d' %total_no)

    # load the invite list (sheet labeled as "RSVP List")
    kws = {'col_names':True, 'row_names':False, 'start_cell':'A3'}
    invite_list = g2d.download(upload_id, wks_name='RSVP List', **kws)

    # normalize the names
    invite_first = invite_list['First'].apply(lambda x: x.lower())
    invite_last  = invite_list['Last'].apply(lambda x: x.lower())

    # open the spreadsheet again
    credentials = g2d.get_credentials()
    gc = gspread.authorize(credentials)
    ssheet = gc.open_by_key(upload_id)

    # get the RSVP list get_worksheet
    ws = [ws for ws in ssheet.worksheets() if ws.title == 'RSVP List'][0]

    # update RSVP values on the 'RSVP List' sheet
    # this changes the RSVP answer to Yes/No in column D of the RSVP List page
    # NOTE: it only changes entries for those who used online RSVP form
    for i, row in df.iterrows():
        first, last = row['Name'].split(maxsplit=1)
        index = (invite_last == last.lower())&(invite_first == first.lower())

        # we found a match in RSVP List
        if index.sum() == 1:
            cell = "D" + str(4 + np.where(index)[0][0])
            ans = "Yes" if row['Yes'] == 1 else "No"
            ws.update_acell(cell, ans)

        # no match between online RSVP form and master list was found!
        elif index.sum() == 0:
            print("warning: %s %s submission has no match in invite list" %(first, last))

        # multiple matches!
        else:
            print("warning: %s %s has multiple match on invite list" %(first, last))

    # print out total
    total_yes = ws.acell('J6').value
    total_no = ws.acell('K6').value
    print("Total YES RSVPS: %s" %total_yes)
    print("Total NO RSVPS: %s" %total_no)


if __name__ == '__main__':

    # read and clean Jotform data
    JOTFORM = "1_hoBn8_0U9kurUFrr3sv6HAR_TCt2GlRL547G4ZZI7w"
    df = clean_jotform(JOTFORM)

    # the YES/NO options on the RSVP form
    YES = "can't wait!"
    NO  = "regretfully, can't make it"

    # get the DataFrame holding the RSVPs
    df = get_rsvps(df, YES, NO)

    # upload the RSVP list to your own google drive
    UPLOAD = "1iEAfk1cVG_PwhcwKJxUeLycUIsRhsAsp9e4xCk2qLtM"
    upload(UPLOAD, df)
