from sklearn.naive_bayes import MultinomialNB
import pandas as pd
import numpy as np
import pickle
import math

def oneHotEncoder(df,filename,cols=None):
    oheDf = pd.get_dummies(data=df,columns=cols)
    # oheDf = pd.DataFrame(data=out,columns=le.classes_)
    # print("OHE columns: ", oheDf.columns)
    # print('OHE size: ', len(oheDf.index))
    # df = pd.concat([df,oheDf])
    # df.drop('BOROUGH')
    oheDf.to_csv(filename, index=False)
    return oheDf

def createBoroughDf(oheDf, filename):
    boroughs = ["BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND"]
    boroughDf = oheDf[["BOROUGH_" + b for b in boroughs]]
    boroughDf.columns = boroughs
    # boroughDf["ACCIDENT"] = pd.Series(data=[1 for i in range(0, len(collisionBoroughDf.index))])
    # print(boroughDf.columns)
    boroughDf.to_csv(filename, index=False)
    return boroughDf

def findProbOfEventInBorough(df):
    n = len(df.index)
    colProbs = {}
    for column in df:
        colProbs[column] = (float)(df[column].sum())/n

    print(colProbs)
    return colProbs

def getBoroughFromCourt(row):
    map = {}
    map["BRONX TVB"] = "BRONX"
    map["BROOKLYN NORTH TVB"] = "BROOKLYN"
    map["BROOKLYN SOUTH TVB"] = "BROOKLYN"
    map["MANHATTAN NORTH TVB"] = "MANHATTAN"
    map["MANHATTAN SOUTH TVB"] = 'MANHATTAN'
    map["RICHMOND TVB"] = "STATEN ISLAND"
    map["QUEENS NORTH TVB"] = "QUEENS"
    map["QUEENS SOUTH TVB"] = "QUEENS"

    return map[row['Court']]

def loadObject(name):
    objects = []
    with open(name + '.pkl', 'rb') as f:
        while True:
            try:
                objects.append(pickle.load(f))
            except EOFError:
                break

    return objects

def convertAllCollisionReasonsToGroups(df):
    reasonCols = ['CONTRIBUTING FACTOR VEHICLE ' + str(i) for i in range(1,6)]
    collision_reasons_to_groups, collision_groups = loadObject('IntermediateData/collision_map')
    tempDf = df.apply(lambda row: convertCollisionReasonsToGroupsForRow(row,collision_reasons_to_groups,collision_groups), axis=1)
    # print(tempDf.columns)

    for col in reasonCols:
        df[col] = tempDf[col]

    df = df.dropna(subset=reasonCols,how='all')
    df.to_csv('ProcessedData/Grouped_Collisions.csv',index=False)
    return df

def convertCollisionReasonsToGroupsForRow(row,collision_reasons_to_groups, collision_groups):
    for i in range(1,6):
        column = 'CONTRIBUTING FACTOR VEHICLE ' + str(i)

        if(not row[column] in collision_reasons_to_groups.keys()):
            row[column] = np.nan
        else:
            row[column] = collision_reasons_to_groups[row[column]]
    return row

def convertAllViolationReasonsToGroups(df):
    reasonCols = ['Violation Description']
    violation_reasons_to_groups, violation_groups = loadObject('IntermediateData/violation_map')
    tempDf = df.apply(lambda row: convertViolationReasonsToGroupsForRow(row,violation_reasons_to_groups,violation_groups), axis=1)
    # print(tempDf.columns)

    for col in reasonCols:
        df[col] = tempDf[col]

    df = df.dropna(subset=reasonCols)
    df.to_csv('ProcessedData/Grouped_Violations.csv',index=False)
    return df

def convertViolationReasonsToGroupsForRow(row,collision_reasons_to_groups, collision_groups):
    for i in range(1,2):
        column = 'Violation Description'

        if(not row[column] in collision_reasons_to_groups.keys()):
            row[column] = np.nan
        else:
            row[column] = collision_reasons_to_groups[row[column]]
    return row

def findLabelCountInCollisionRow(row, label):
    count = 0
    for i in range(1,6):
        column = 'CONTRIBUTING FACTOR VEHICLE ' + str(i)
        if(row[column] == label):
            count = count + 1
    return count

def trainCollisionModel(df,trainingLabel,borough):
    filteredDf = df.loc[df['BOROUGH'] == borough]
    countSeries = filteredDf.apply(lambda row: findLabelCountInCollisionRow(row, trainingLabel), axis=1)
    prob = countSeries.sum()

    filteredFactors = []
    numRows = 0
    for i in range(1,6):
        column = 'CONTRIBUTING FACTOR VEHICLE ' + str(i)

        temp = filteredDf[column].as_matrix()
        # print(len(temp[np.isnan(temp)]))
        filteredFactor = temp[~np.isnan(temp)]
        # filteredFactor = filter(lambda a: a not in [i for i in range(0,11)], filteredDf[column].tolist())
        # print(type(filteredFactor[0]))
        # print(str(i) + ": " + str(len(filteredDf[column].tolist())))
        # print(str(i) + ": " + str(len(filteredFactor)))
        numRows = numRows + len(filteredFactor)
        filteredFactors.append(filteredFactor)

    # prob = prob/(5.0*len(filteredDf.index))
    prob = prob / (1.0 * numRows)
    return prob

def findProbOfAccidentReasonsInBoroughs(df):
    probs = {}
    for borough in ["BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND"]:
        probs[borough] = []
        for group in range(0,11):
            probs[borough].append(trainCollisionModel(df,group,borough))

    print(probs)
    return probs

def findLabelCountInViolationRow(row, label):
    count = 0
    for i in range(1,2):
        column = 'Violation Description'
        if(row[column] == label):
            count = count + 1
    return count

def trainViolationModel(df,trainingLabel,borough):
    filteredDf = df.loc[df['BOROUGH'] == borough]
    countSeries = filteredDf.apply(lambda row: findLabelCountInViolationRow(row, trainingLabel), axis=1)
    prob = countSeries.sum()

    column = 'Violation Description'
    temp = filteredDf[column].as_matrix()
    # print(len(temp[np.isnan(temp)]))
    filteredFactor = temp[~np.isnan(temp)]
    # filteredFactor = filter(lambda a: a not in [i for i in range(1,31)], filteredDf[column].tolist())
    # print(type(filteredFactor[0]))
    # print(str(i) + ": " + str(len(filteredDf[column].tolist())))
    # print(str(i) + ": " + str(len(filteredFactor)))
    numRows = len(filteredFactor)

    # prob = prob/(1.0*len(filteredDf.index))
    prob = prob / (1.0 * numRows)
    return prob

def findProbOfViolationReasonsInBoroughs(df):
    probs = {}
    for borough in ["BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND"]:
        probs[borough] = []
        for group in range(1,31):
            probs[borough].append(trainViolationModel(df,group,borough))

    print(probs)
    return probs

def findTopAccidentGroups(probs):
    collision_reasons_to_groups, collision_groups = loadObject('IntermediateData/collision_map')

    topAccidents = {}
    for borough in probs.keys():
        groupToProb = {}
        for i in range(0,len(probs[borough])):
            groupToProb[collision_groups[i]] = probs[borough][i]

        # sortedGroupToProb = sorted(groupToProb, key=groupToProb.get,reverse=True)
        topAccidents[borough] = []
        # index = 1
        for group in sorted(groupToProb, key=groupToProb.get,reverse=True):
            # if(index <= 5):
            topAccidents[borough].append(group)
            # else:
            #     break

    print(topAccidents)
    return topAccidents

def findTopViolationGroups(probs):
    violation_reasons_to_groups, violation_groups = loadObject('IntermediateData/violation_map')

    topViolations = {}
    for borough in probs.keys():
        groupToProb = {}
        for i in range(0,len(probs[borough])):
            groupToProb[violation_groups[i]] = probs[borough][i]

        # sortedGroupToProb = sorted(groupToProb, key=groupToProb.get,reverse=True)
        topViolations[borough] = []
        index = 1
        for group in sorted(groupToProb, key=groupToProb.get,reverse=True):
            if(index <= 11):
                topViolations[borough].append(group)
                index = index + 1
            else:
                break

    print(topViolations)
    return topViolations

def mergeTopAccidentsAndTopViolations(topAccidents, topViolations):
    # collision_reasons_to_groups, collision_groups = loadObject('IntermediateData/collision_map')
    violation_reasons_to_groups, violation_groups = loadObject('IntermediateData/violation_map')
    collision_to_violation_map = loadObject('IntermediateData/collision_to_violation_map')[0]

    topAccidentsAndViolations = {}

    print(topAccidents.keys())
    for borough in topAccidents.keys():
        print(borough)
        topAccidentsAndViolations[borough + "_ACCIDENTS"] = []
        topAccidentsAndViolations[borough + "_VIOLATIONS"] = []

        accidentGroups = topAccidents[borough]
        violationGroups = topViolations[borough]

        # accidentGroups = [collision_reasons_to_groups[accident] for accident in accidents]
        # violationGroups = [violation_reasons_to_groups[violation] for violation in violations]

        for i in range(0,len(accidentGroups)):
            accidentGroup = accidentGroups[i]
            topAccidentsAndViolations[borough + "_ACCIDENTS"].append(str(i+1) + ". " + accidentGroup)

            mappedViolations = collision_to_violation_map[accidentGroup]
            indices = [i for i,x in enumerate(mappedViolations) if x == 1]
            mappedViolationGroups = [violation_groups[i + 1] for i in indices]

            j = 0
            while(j < len(violationGroups)):
                if(violationGroups[j] in mappedViolationGroups):
                    topAccidentsAndViolations[borough + "_VIOLATIONS"].append(str(j + 1) + ". " + violationGroups[j])
                    break
                j = j + 1

            if(j == len(violationGroups)):
                topAccidentsAndViolations[borough + "_VIOLATIONS"].append(str(j + 1) + ". ")

    return topAccidentsAndViolations

# TODO: Do not consider empty contributing factors in probability calculation
if __name__ == "__main__":
    # collisionDf = pd.read_csv("ProcessedData/NYPD_Motor_Vehicle_Collisions.csv", low_memory=False)
    # convertAllCollisionReasonsToGroups(collisionDf)


    collisionDf = pd.read_csv("ProcessedData/Grouped_Collisions.csv", low_memory=False)

    collisionColsList = ['BOROUGH']
    reasons = ['CONTRIBUTING FACTOR VEHICLE ' + str(i) for i in range(1,6)]
    for reason in reasons:
        collisionColsList.append(reason)

    collisionDf = collisionDf[collisionColsList]



    # collisionOheDf = oneHotEncoder(collisionDf,'IntermediateData/collision_ohe.csv')
    # collisionBoroughDf = createBoroughDf(collisionOheDf,"IntermediateData/collisionBorough.csv")


    # collisionOheDf = pd.read_csv('IntermediateData/collision_ohe.csv')
    # collisionBoroughDf = pd.read_csv("IntermediateData/collisionBorough.csv")

    # findProbOfEventInBorough(collisionBoroughDf)


    ticketDf = pd.read_csv("ProcessedData/Grouped_Violations.csv", low_memory=False)



    # ticketDf = pd.read_csv("ProcessedData/Traffic_Tickets_Issued__Four_Year_Window - Copy.csv", low_memory=False)
    # courts = ["BRONX TVB","BROOKLYN NORTH TVB","BROOKLYN SOUTH TVB","MANHATTAN NORTH TVB","MANHATTAN SOUTH TVB","RICHMOND TVB","QUEENS NORTH TVB","QUEENS SOUTH TVB"]
    # # print("Ticket columns: " + str(ticketDf.columns))
    # # print("Unique courts: " + str(len(ticketDf['Court'].unique())))
    #
    # nycticketDf = ticketDf.loc[ticketDf['Court'].isin(courts)]
    #
    # convertAllViolationReasonsToGroups(nycticketDf)
    # # print("NYC courts: " + str(nycticketDf['Court'].unique()))


    ticketColsList = ['Violation Charged Code','Violation Description','Court']
    ticketDf = ticketDf[ticketColsList]
    ticketDf["BOROUGH"] = ticketDf.apply(lambda row: getBoroughFromCourt(row), axis=1)


    # print("NYC boroughs: " + str(nycticketDf['BOROUGH'].unique()))
    # print("NYC ticket reasons: " + str(len(nycticketDf['Violation Description'].unique())))
    # nycticketDf.to_csv('ticketdf.csv',index=False)

    # ticketOheDf = oneHotEncoder(ticketDf,'IntermediateData/ticket_ohe.csv',['BOROUGH'])
    # ticketBoroughDf = createBoroughDf(ticketOheDf, "IntermediateData/ticketBorough.csv")
    # findProbOfEventInBorough(ticketBoroughDf)


    accidentProbs = findProbOfAccidentReasonsInBoroughs(collisionDf)
    violationProbs = findProbOfViolationReasonsInBoroughs(ticketDf)

    topAccidents = findTopAccidentGroups(accidentProbs)
    topViolations = findTopViolationGroups(violationProbs)

    topAccidentsDf = pd.DataFrame.from_dict(topAccidents)
    topViolationsDf = pd.DataFrame.from_dict(topViolations)

    topAccidentsDf.to_csv('InferredData/topAccidents.csv',index=False)
    topViolationsDf.to_csv('InferredData/topViolations.csv', index=False)



    # topAccidentsDf = pd.read_csv('InferredData/topAccidents.csv')
    # topViolationsDf = pd.read_csv('InferredData/topViolations.csv')
    # topAccidents = topAccidentsDf.to_dict(orient='list')
    # topViolations = topViolationsDf.to_dict(orient='list')

    topAccidentsAndViolations = mergeTopAccidentsAndTopViolations(topAccidents,topViolations)
    topAccidentsAndViolationsDf = pd.DataFrame.from_dict(topAccidentsAndViolations)
    topAccidentsAndViolationsDf.to_csv('InferredData/topAccidents&Violations.csv',index=False)







