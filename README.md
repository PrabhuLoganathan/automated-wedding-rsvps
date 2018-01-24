# Automated Wedding RSVPs with JotForm, pandas, and Google docs

For more details, see [this blog post](http://nickhand.github.io/blog/pages/2018/01/10/automating-wedding-rsvps/).

# Requirements

You'll need Python 2/3 and `df2gspread` installed. I recommend using [Anaconda](https://www.anaconda.com/download) for your Python manager. The necessary requirements can be installed using:

```
pip install df2gspread
```

# User's Guide

To setup a version of this system for yourself, there are a few steps required. These steps are:

1. Setup a [JotForm](www.jotform.com) account and clone the Wedding RSVP template form discussed in this post. The template is available [here](https://www.jotform.com/form-templates/wedding-rsvp-template).
2. For each guest on your guest list, add conditional logic to the form to show the desired Yes/No fields based on the "First Name" and "Last Name" input values.
3. Add the "Google Drive" integration for your form and take note of the unique identifier of the output spreadsheet. 
4. Copy the "master" guest list spreadsheet template (available [here](https://drive.google.com/open?id=1iEAfk1cVG_PwhcwKJxUeLycUIsRhsAsp9e4xCk2qLtM)) to your own Google Drive, and input your guest list on the "RSVP List" sheet. Take note of the unique identifier of the cloned spreadsheet. 
5. Setup Google Drive API credentials, following the instructions [here](http://df2gspread.readthedocs.io/en/latest/overview.html#access-credentials).
6. Download the ``compute_rsvps.py`` script and make sure the requirements are also installed.
7. At the bottom of the ``compute_rsvps.py`` script, update the "YES" and "NO" variables with the RSVP messages you used on your form. Also, update the "JOTFORM" variable with the identifier of the spreadsheet output by JotForm (see step #3), and update the "UPLOAD" variable with the identifier of the final spreadsheet that holds the master guest list (see step #4). 
8. Run the ``compute_rsvps.py`` whenever a new submission is received. 
9. Sit back and relax! (Or plan the rest of your wedding.)
