import xml.sax
import pandas as pd
import xml.etree.ElementTree as ET


def extract_docs(index, doc):
    if index == 0:
        return extract_first_doc(index, doc)
    elif index == 1:
        return extract_second_doc(index, doc)
    elif index == 2:
        return extract_third_doc(index, doc)
    elif index == 3:
        return extract_fourth_doc(index, doc)
    elif index == 4:
        return extract_fifth_doc(index, doc)
    elif index == 5:
        return extract_sixth_doc(index, doc)
    elif index == 6:
        return extract_seventh_doc(index, doc)


def extract_first_doc(doc):

    namespaces = {"ss:": "urn:schemas-microsoft-com:office:spreadsheet"}

    tree = ET.parse(doc)

    root = tree.getroot()

    res_dict = {}

    # get the subelement of the first element

    row_id = 0

    for child in root[3][0]:

        if (
            child.attrib.get("{urn:schemas-microsoft-com:office:spreadsheet}StyleID")
            is None
        ):
            row = []
            for subchild in child:

                row.append(subchild[0].text)
            res_dict[row_id] = row

            row_id += 1

    df = pd.DataFrame.from_dict(res_dict, orient="index")

    # drop the first row
    df.drop(0, inplace=True)

    # first row as header
    df.columns = df.iloc[0]

    # drop the first row
    df.drop(1, inplace=True)

    # first 4 columns
    df = df.iloc[:, :4]

    # rename columns
    df.columns.values[1] = "Produktname (intern)"
    df.columns.values[3] = "Produktkategorien (intern)"

    return df


def extract_second_doc(doc):
    namespaces = {"ss:": "urn:schemas-microsoft-com:office:spreadsheet"}
    tree = ET.parse(doc)

    root = tree.getroot()

    res_dict = {}

    # get the subelement of the first element
    row_id = 0
    for child in root[3][0]:
        if (
            child.attrib.get("{urn:schemas-microsoft-com:office:spreadsheet}StyleID")
            is None
        ):
            row = []
            for subchild in child:
                row.append(subchild[0].text)
            res_dict[row_id] = row
            row_id += 1

    df = pd.DataFrame.from_dict(res_dict, orient="index")

    # drop the first three rows
    df.drop([0, 1, 2], inplace=True)

    # first row as header
    df.columns = df.iloc[0]

    # drop the first row
    df.drop(3, inplace=True)

    df = df[df["Mengenart"] == "Produkteinheit"].reset_index(drop=True)

    return df


def extract_third_doc(doc):
    return


def extract_fourth_doc(doc):
    return


def extract_fifth_doc(doc):
    return


def extract_sixth_doc(doc):
    return


def extract_seventh_doc(doc):
    return
