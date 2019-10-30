# coding=UTF-8
import re

from appJar import gui
from netaddr import *

# globals
IPOutput = IPSet()

# constants
# App Windows
GUI_MAIN = 'IPv4 Calculator'
# Label Frames
LF_WORKAREA = 'Work Area'
LF_IPLIST = 'IP List'
# Buttons
BT_ADD = 'Add to List \u21E9'
BT_REMOVE = 'Remove from list \u21EA'
BT_CLEAR = 'Clear List X'
# Radio Buttons
RB_DISPLAYAS = 'DisplayAs'
RB_DA_BYCIDR = 'By CIDR'
RB_DA_BYRANGE = 'By Range'
RB_DA_MIXED = 'Mixed'

RB_DISPLAYUSING = 'DisplayUsing'
RB_DU_COMMASEPERATED = 'Comma Separated'
RB_DU_SEPERATELINES = 'Separate Lines'
# TextAreas
TA_WORKING = 'Working'
TA_IPLIST = 'IP List'
# Messages
MSG_IPERRORHDR = 'Validation Error'
MSG_IPERROR = 'Error in IP/CIDR: '


# IP Address validator.  Returns an IPAddress or False
def validate_ip(ip):
    number = ip.split('.')

    if len(number) != 4:
        return False

    try:
        for byte in number:
            if not (0 <= int(byte) <= 255):
                return False
    except:
        return False

    return IPAddress('.'.join(number))


# IP Address Range validator.  Returns an IPRange, an IPAddress or False
def validate_ip_range(ip_range):
    if '-' not in ip_range:
        return False

    start_ip, end_ip = [validate_ip(ip) for ip in ip_range.split('-')]

    if not start_ip or not end_ip or start_ip > end_ip:
        return False

    if start_ip == end_ip:
        return start_ip

    return IPRange(start_ip, end_ip)


# IP Address CIDR validator.  Returns an IPAddress, IPNetwork or False
def validate_ip_cidr(ipcidr):
    if '/' not in ipcidr:
        return False

    ip, cidr = ipcidr.split('/')
    cidr = int(cidr)

    if not (0 <= cidr <= 32) or not validate_ip(ip):
        return False

    if cidr == 32:
        return IPAddress(ip)
    else:
        return IPNetwork(ipcidr)


# IP Address List validator.  Returns an IPSet or False
def validate_ip_list(ip_list):
    ip_list = re.sub(r'\.\.\.', '-', ip_list)  # Replace triple dots (...) with a '-'
    ip_list = re.sub('\u2026', '-', ip_list)  # Replace an ellipsis (…) with a '-'
    ip_list = re.sub('to', '-', ip_list)  # Replace instances of 'to' with a '-'
    ip_list = re.sub(r'\s*-\s*', '-', ip_list)  # Remove whitespace aground '-'
    ip_list = re.sub(r'\s', ',', ip_list)  # Replace all whitespace with ','
    ip_list = re.sub(',{2,}', ',', ip_list)  # Remove repeated ','s

    processed_list = []

    for item in ip_list.split(','):
        if item == '':
            continue
        elif '/' in item:
            test = validate_ip_cidr(item)
        elif '-' in item:
            test = validate_ip_range(item)
        else:
            test = validate_ip(item)

        if test:
            if isinstance(test, IPRange):
                processed_list.append(test)
            if isinstance(test, IPAddress):
                processed_list.append(IPRange(str(test), str(test)))
            if isinstance(test, IPNetwork):
                processed_list.append(IPRange(test.first, test.last))
        else:
            app.errorBox(MSG_IPERRORHDR, MSG_IPERROR + item)
            return False

    return IPSet([cidr for ip in processed_list for cidr in ip.cidrs()])


# Formats a list of CIDR Addressees, removing "/32"
def format_cidr_list(cidr_list):
    formattedList = []
    for item in cidr_list:
        formattedList.append(str(item).split('/32')[0])

    return ','.join(formattedList)


def format_range_list(range_list):
    formatted_list = []
    for item in range_list:
        if item.first == item.last:
            formatted_list.append(str(IPAddress(item.first)))
        else:
            formatted_list.append(str(item))

    return ','.join(formatted_list)


def format_mixed_list(range_list):
    formatted_list = []
    # TODO: Write Mixed format function
    return ','.join(formatted_list)


# Updates the "IP List" TextBox
def update_ip_list():
    name = app.getRadioButton(RB_DISPLAYAS)
    display_format = app.getRadioButton(RB_DISPLAYUSING)

    app.clearTextArea(TA_IPLIST)
    if name == RB_DA_BYCIDR:
        formatted_list = format_cidr_list(IPOutput.iter_cidrs())
    elif name == RB_DA_BYRANGE:
        formatted_list = format_range_list(IPOutput.iter_ipranges())
    elif name == RB_DA_MIXED:
        formatted_list = format_mixed_list(IPOutput.iter_ipranges())
    else:
        raise RuntimeError('Invalid value for DisplayAs Radio Button')

    if display_format == RB_DU_SEPERATELINES:
        formatted_list = formatted_list.replace(',', '\n')

    app.setTextArea(TA_IPLIST, formatted_list)


# Handler Events
def buttonpress(name):
    global IPOutput
    try:
        if name == BT_ADD:
            IPOutput = IPOutput.union(validate_ip_list(app.getTextArea(TA_WORKING)))
        elif name == BT_REMOVE:
            IPOutput -= validate_ip_list(app.getTextArea(TA_WORKING))
        elif name == BT_CLEAR:
            IPOutput.clear()
    except:
        return

    IPOutput.compact()
    update_ip_list()


# gui builder
# - Main GUI
with gui(GUI_MAIN) as app:
    app.setResizable(False)

    app.setFont(20)
    app.setButtonFont(15)

    with app.labelFrame(LF_WORKAREA, colspan=3, stretch='column', sticky='news'):
        app.addScrolledTextArea(TA_WORKING)
        app.getTextAreaWidget(TA_WORKING).config(font=12)

    app.addButtons([BT_ADD, BT_REMOVE, BT_CLEAR], buttonpress, colspan=3)

    with app.labelFrame(LF_IPLIST, colspan=3, stretch='column', sticky='news'):
        app.addScrolledTextArea(TA_IPLIST)
        app.getTextAreaWidget(TA_IPLIST).config(font=12)

    row = app.getRow()
    app.addRadioButton(title=RB_DISPLAYAS, name=RB_DA_BYCIDR, row=row, column=0)
    app.addRadioButton(title=RB_DISPLAYAS, name=RB_DA_BYRANGE, row=row, column=1)
    app.addRadioButton(title=RB_DISPLAYAS, name=RB_DA_MIXED, row=row, column=2)

    app.setRadioButtonChangeFunction(RB_DISPLAYAS, lambda name: update_ip_list())
    # for button in app.getRadioButtonWidget(RB_DISPLAYAS):
    # button.setFont(size="15")
    # button.config(font="15")

    row = row + 1
    app.addRadioButton(title=RB_DISPLAYUSING, name=RB_DU_SEPERATELINES, row=row, column=0)
    app.addRadioButton(title=RB_DISPLAYUSING, name=RB_DU_COMMASEPERATED, row=row, column=1)
    app.setRadioButtonChangeFunction(RB_DISPLAYUSING, lambda name: update_ip_list())
    # for button in app.getRadioButton(RB_DISPLAYUSING):
    # button.setFont(siz="15")
    # button.config(font="15")

    app.setTextAreaWidths([TA_WORKING, TA_IPLIST], 50)
