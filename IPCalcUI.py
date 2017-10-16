# coding=UTF-8
from appJar import gui
from netaddr import *
import re

# globals
IPOutput = IPSet()

# constants
# Buttons
BT_ADD = "Add to List ⇩"
BT_REMOVE = "Remove from list ⇪"
BT_CLEAR = "Clear List X"
# Radio Buttons
RB_DISPLAYAS = "DisplayAs"
RB_DA_BYCIDR = "By CIDR"
RB_DA_BYRANGE = "By Range"

RB_DISPLAYUSING = "DisplayUsing"
RB_DU_COMMASEPERATED = "Comma Separated"
RB_DU_SEPERATELINES = "Separate Lines"
# TextAreas
TA_WORKING = "Working"
TA_IPLIST = "IP List"
# Messages
MSG_IPERRORHDR = "Validation Error"
MSG_IPERROR = "Error in IP/CIDR: "


# IP Address validator.  Returns an IPAddress or False
def validate_ip(ip):
    number = ip.split(".")

    if len(number) != 4:
        return False

    try:
        for byte in number:
            if int(byte) < 0 or int(byte) > 255:
                return False
    except:
        return False

    return IPAddress('.'.join(number))


# IP Address Range validator.  Returns an IPRange, an IPAddress or False
def validate_ip_range(iprange):
    if '-' not in iprange:
        return False

    start_ip = validate_ip(iprange.split('-')[0])
    end_ip = validate_ip(iprange.split('-')[1])

    if start_ip is False or end_ip is False or start_ip > end_ip:
        return False

    if start_ip == end_ip:
        return start_ip

    return IPRange(start_ip, end_ip)


# IP Address CIDR validator.  Returns an IPAddress, IPNetwork or False
def validate_ip_cidr(ipcidr):
    if '/' not in ipcidr:
        return False

    ip = ipcidr.split('/')[0]
    cidr = int(ipcidr.split('/')[1])

    if validate_ip(ip) is False or cidr > 32 or cidr < 0:
        return False

    if cidr == 32:
        return IPAddress(ip)
    else:
        return IPNetwork(ipcidr)


# IP Address List validator.  Returns an IPSet or False
def validate_ip_list(iplist):
    iplist = re.sub(ur"\s*-\s*", "-", iplist)  # Remove whitespace aground '-'
    iplist = re.sub(ur"\s", ",", iplist)  # Replace all whitespace with ','
    iplist = re.sub(ur",{2,}", ",", iplist)  # Remove repeated ','s

    processed_list = IPSet()

    for item in iplist.split(','):
        if item == '':
            continue
        elif '/' in item:
            test = validate_ip_cidr(item)
        elif '-' in item:
            test = validate_ip_range(item)
        else:
            test = validate_ip(item)

        if test is not False:
            processed_list.add(test)
        else:
            app_main.errorBox(MSG_IPERRORHDR, MSG_IPERROR + item)
            return False

    return processed_list


# Formats a list of CIDR Addressees, removing "/32"
def format_cidr_list(list):
    formattedList = []
    for item in list:
        formattedList.append(str(item).split("/32")[0])

    return ','.join(formattedList)


def format_range_list(list):
    formatted_list = []
    for item in list:
        if item._start == item._end:
            formatted_list.append(str(item._start))
        else:
            formatted_list.append(str(item))

    return ','.join(formatted_list)


# Updates the "IP List" TextBox
def update_ip_list():
    name = app_main.getRadioButton(RB_DISPLAYAS)
    format = app_main.getRadioButton(RB_DISPLAYUSING)

    app_main.clearTextArea(TA_IPLIST)
    if name == RB_DA_BYCIDR:
        formatted_list = format_cidr_list(IPOutput.iter_cidrs())
    else:
        formatted_list = format_range_list(IPOutput.iter_ipranges())

    if format == RB_DU_SEPERATELINES:
        formatted_list = formatted_list.replace(",", "\n")

    app_main.setTextArea(TA_IPLIST, formatted_list)


# Wrapper for control to ignore 'name'
def update_ip_list_control(name):
    update_ip_list()


# Handler Events
def buttonpress(name):
    global IPOutput
    try:
        if name == BT_ADD:
            IPOutput = IPOutput.union(validate_ip_list(app_main.getTextArea(TA_WORKING)))
        elif name == BT_REMOVE:
            IPOutput -= validate_ip_list(app_main.getTextArea(TA_WORKING))
        elif name == BT_CLEAR:
            IPOutput.clear()
    except:
        return

    IPOutput.compact()
    update_ip_list()


# gui builder
# - Main GUI
app_main = gui("IP Calculator")
app_main.setResizable(False)

app_main.setFont(20)
app_main.setButtonFont(15)

app_main.startLabelFrame("Work Area", colspan=2)
app_main.addScrolledTextArea(TA_WORKING)
app_main.getTextAreaWidget(TA_WORKING).config(font=12)
app_main.stopLabelFrame()

app_main.addButtons([BT_ADD, BT_REMOVE, BT_CLEAR], buttonpress, colspan=2)

app_main.startLabelFrame("IP List", colspan=2)
app_main.addScrolledTextArea(TA_IPLIST)
app_main.getTextAreaWidget(TA_IPLIST).config(font=12)
app_main.stopLabelFrame()

row = app_main.getRow()
app_main.addRadioButton(RB_DISPLAYAS, RB_DA_BYCIDR, row, 0)
app_main.addRadioButton(RB_DISPLAYAS, RB_DA_BYRANGE, row, 1)
app_main.setRadioButtonChangeFunction(RB_DISPLAYAS, update_ip_list_control)
for button in app_main.getRadioButtonWidget(RB_DISPLAYAS):
    button.configure(font=15)

row = row + 1
app_main.addRadioButton(RB_DISPLAYUSING, RB_DU_SEPERATELINES, row, 0)
app_main.addRadioButton(RB_DISPLAYUSING, RB_DU_COMMASEPERATED, row, 1)
app_main.setRadioButtonChangeFunction(RB_DISPLAYUSING, update_ip_list_control)
for button in app_main.getRadioButtonWidget(RB_DISPLAYUSING):
    button.configure(font=15)

app_main.setTextAreaWidths([TA_WORKING, TA_IPLIST], 50)

app_main.go()
