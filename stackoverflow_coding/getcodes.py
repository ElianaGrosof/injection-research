'''
getcodes.py
@authors Eliana Grosof (author), Sam Fertig (revision)
December 2019-June 2020
This program retrieves user-inputted SS codes for a StackOverflow page and enters the sanitized data
into a SQL database. The program constructs a SQL query as a Python string, then writes the query to a
bash script, and then runs the bash script. 
'''
# **********************************************************
import re
import subprocess
import os

# **********************************************************
# Returns integer value of StackOverflow page id.
def getId():
    goodInput = False
    while not goodInput:
        id = input("Page ID: ")
        if representInt(id):
            validinput = True
            return int(id)
        else:
            print("Bad input. Try again.")

# **********************************************************
# Gets and returns codes for each page section: question, answer, and everything else.
def getinput():
    Qcodes = input("QUESTION: ")
    Acodes = input("ANSWER: ")
    EEcodes = input("EVERYTHING ELSE: ")
    return [Qcodes, Acodes, EEcodes]

# **********************************************************
# Checks that the coder name is not misspelled and cleans the input.
def checkcoder(question):
    validinput = False
    while not validinput:
        coder = input(question)
        cleancoder = coder.strip().lower()
        if cleancoder in ['eliana', 'sam', 'evans']:
            validinput = True
            return cleancoder
        else:
            print("Invalid input. Please try again.")

# **********************************************************
# Cleans up messy string; preferably space separated.
def cleaninput(inputstr):
    inputarr = inputstr.split()
    cleanarr = []
    for i in inputarr:
        newi = re.sub('[^A-Za-z0-9]+', '', i)
        cleanarr.append(newi)
    return cleanarr

# **********************************************************
# Handles a (y/n) scenario. Takes as input a yes/no question, returns "y" or "n".
def ynans(question):
    validinput = False
    while not validinput:
        r = input(question)
        strippedr = r.strip()
        if (strippedr in "yn") and (len(strippedr) > 0):
            validinput = True
            return r
        else:
            print("Bad input. Input only \"y\" or \"n\".")

# **********************************************************
# Checks if the number is an integer. Helper function to "getId".
def representInt(str):
    try:
        int(str)
        return True
    except ValueError:
        return False

# **********************************************************
# Takes an array of user-inputted codes (or code abbreviations) and returns the formatted, database-ready codes.
def checkcodes(codearr, type):
    codelist = ['sql_injectable', 'mentions_sqli', 'real_escape', 'link', 'code_snippet', 'prepared','bounded_user_input']

    # Abbreviation map
    abbmap = {'si': 'sql_injectable',
          'ms':'mentions_sqli',
          're':'real_escape',
          'li': 'link',
          'co': 'code_snippet',
          'pr': 'prepared',
          'codesnippet': 'code_snippet',
          'bui': 'bounded_user_input',
          'bounded': 'bounded_user_input'}
    realcodes = []

    # Start mappin'
    realcodes = []
    #get mappings out
    for i in codearr:
        if (i in codelist):
            realcodes.append(i)
        elif (i in abbmap):
            realcodes.append(abbmap[i])
        else:
            continue

    # Remove duplicates.
    realcodes = list(set(realcodes))

    return realcodes

# **********************************************************
def constructquery(codes, typestr, Id, coder):
    ID = str(Id)
    query = ''
    delete = ''

    orderedfields = ['sql_injectable', 'real_escape', 'link', 'code_snippet','prepared','mentions_sqli','bounded_user_input']
    realvalues = [0]*7 #holds actual codes to be entered into database
    for codeindex in range(0, len(orderedfields)):
        if orderedfields[codeindex] in codes:
            realvalues[codeindex] = 1

    query = 'INSERT INTO initial_socodes (coder, id, url, relevant, type, sql_injectable, real_escape, link, code_snippet, prepared, mentions_sqli, bounded_user_input) VALUES' + " ( '"+coder+"',"+ID+','+"'https://stackoverflow.com/q/"+str(ID) +"'," + '1' + ",'" + typestr + "'," + str(realvalues[0]) + ',' + str(realvalues[1]) + ',' + str(realvalues[2]) + ',' + str(realvalues[3]) + ',' + str(realvalues[4]) + ',' + str(realvalues[5]) + ',' + str(realvalues[6]) + ');'
    return query

# *********************************************************
def constructirrelevant(Id, coder):
    ID = str(Id)
    query = 'INSERT INTO initial_socodes (coder, id, url, relevant, type, sql_injectable, real_escape, link, code_snippet, prepared, mentions_sqli, bounded_user_input) VALUES' + "( '" +coder+"'," + ID + ',' + "'https://stackoverflow.com/q/"+ ID + "'," + '0' + ",'" + 'irrelevant' + "',0,0,0,0,0,0,0);"
    return query

# **********************************************************
# runquery() runs the query.
# Writes a bash script (query.sh), makes it executable using existing bash script (addpermissions.sh).
def runquery(query):

    # Write query to file
    f= open("query.sh","w+")
    f.write("#!/bin/bash"+"\n")
    f.write("mysql -uroot -p4TH6iegWki <<EOF" + "\n")
    f.write("use stackoverflow;"+"\n")
    f.write(query +"\n")
    f.write("EOF")
    f.close()

    # Run query.
    subprocess.run("./addpermission.sh", shell=True)

# **********************************************************
def main():
    coder = checkcoder("What's your first name? ")
    end = ""
    while end != "end":
        end = input("Type 'end' to quit. Otherwise, hit enter. \n")
        if end == "end":
            print("Process ended.")
            return
        confirmed = ""
        ID = getId()
        relevance = ynans("Is this question relevant? (y/n)  ")
        if relevance.replace(" ", "") == 'y':
            codes = getinput()
            cleanQCodes = cleaninput(codes[0])
            cleanACodes = cleaninput(codes[1])
            cleanEECodes = cleaninput(codes[2])

            Qcodes = checkcodes(cleanQCodes, 'question')
            Acodes = checkcodes(cleanACodes, 'answer')
            EEcodes = checkcodes(cleanEECodes, 'everything_else')

            #gives opportunity to redo it
            def confirm():
                print("QUESTION: ", Qcodes)
                print("ANSWER: ", Acodes)
                print("EVERYTHING ELSE ", EEcodes)
                confirmed = ynans("Are these codes correct? (y/n)  ")
                return confirmed
            confirmed = confirm()
            if confirmed == 'n':
                continue
            else:
                querylist = []
                Qquery = constructquery(Qcodes, "question", ID, coder)
                Aquery = constructquery(Acodes, "answer", ID, coder)
                EEquery = constructquery(EEcodes, "everything_else", ID, coder)

                #run script
                runquery(Qquery)
                runquery(Aquery)
                runquery(EEquery)

        else:
            query = constructirrelevant(ID, coder)
            runquery(query)
    return

# *****
main()
