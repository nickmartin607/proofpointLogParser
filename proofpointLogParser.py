import sys, re, gzip, argparse
from datetime import datetime, timedelta, date as dt_date

LOG_ARCHIVE = ''
LOG_CURRENT = ''
YELLOW = '\033[33;1m'
CYAN = '\033[36;1m'
RED = '\033[31;1m'
BOLD = '\033[1m'
RESET = '\033[0m'



def main(qid, date):
    
    # Date
    date = datetime.strptime(date, '%Y%m%d').date() if date else dt_date.today()

    # Open Log
    adj_date = date + timedelta(days=1)
    if adj_date > dt_date.today():
        log_name = LOG_CURRENT
        log = open(LOG_CURRENT, 'rb')
    else:
        log_name = re.sub('DATE', adj_date.strftime('%Y%m%d'), LOG_ARCHIVE)
        log = gzip.open(log_name, 'rb')
    # Search Log
    entries = '\\n'.join([re.sub(r'\\n', '', entry) for entry in log if re.search(qid, entry)])
    # Close Log
    log.close()
    # Verify matching entries were found
    if len(entries) == 0:
        print "No entries matching the QID {} in the log {}.".format(qid, log_name)
        return

    # Source/Sender Fields
    src_dst_regex = '=<?([^\s>,]*).*? relay=(\S* \[[\d.]*\])'
    src = re.search(': from' + src_dst_regex, entries).groups() if re.search(': from', entries) else None
    dst = re.search(': to' + src_dst_regex, entries).groups() if re.search(': to', entries) else None

    # Date Field
    date_regex = re.compile('^(\S* \S* \S*)')
    date = date_regex.search(entries).group(1)

    # Attachment Fields
    attachment_regex = re.compile('file=(\S*).*? type=(\S*).*? size=(\S*).*? a=([1-9]).*?')
    attachments_regex = re.compile('(mod=mail cmd=attachment .*? a=[1-9][0-9]*?)')
    attachments = attachments_regex.findall(entries) if attachments_regex.search(entries) else None
    attachments = [attachment_regex.search(a).groups() for a in attachments] if attachments else None
    
    # Status Fields
    status_regex = re.compile('stat=(.*?) \((.*?)\)')
    status = status_regex.search(entries).groups()
    status_details_regex = re.compile('(\S+ \S+) (.*)' if re.search('InternalId', status[1]) else '(\S+) (.*)')
    status_details = status_details_regex.search(status[1]).groups()

    # Spam Details Fields
    spam_details_regex = re.compile('Spam-Details: (.*?) engine=')
    spam_detail_regex = re.compile('(.*)=(.*)')
    spam_details = spam_details_regex.search(entries) if spam_details_regex.search(entries) else None
    spam_details = [spam_detail_regex.search(d).groups() for d in sorted(spam_details.group(1).split(' '))] if spam_details else None


    # Print Format Strings
    heading = "\n" + YELLOW + "  {:<13}" + RESET
    field = CYAN + "{: >15}" + RESET + "  {: <27}"
    field_attachment = "{:3} {:4}KB  {}"
    
    # Printout
    print heading.format("Details")
    print field.format("QID:", qid)
    print field.format("MsgID:", status_details[0])
    print field.format("Date:", date)
    print field.format("Status:", "{}, {}".format(status[0], status_details[1]))
    print heading.format("Source")
    print field.format("Address:", src[0])
    print field.format("Relay:", src[1])
    print heading.format("Destination")
    print field.format("Address:", dst[0])
    print field.format("Relay:", dst[1])
    
    if attachments:
        print heading.format("Attachments")
        for a in attachments:
            print field.format(a[3], field_attachment.format(a[1], int(a[2]) / 1000, a[0]))
    if spam_details:
        print heading.format("Spam Details")
        sd = []
        for k, v in spam_details:
            v = "{}{: <27}{}".format(RED, v, RESET) if (v.isdigit() or v[1:].isdigit()) and int(v) != 0 else v 
            sd.append(field.format(k, v))
        if len(sd) % 2 == 1:
            sd.append("")
        for i in range(0, len(sd), 2):
            print sd[i] if i + 1 == len(sd) else sd[i] + sd[i+1] 
    print ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Search Proofpoint Logs.', add_help=False)
    parser.add_argument('qid', type=str, help="The email QID")
    parser.add_argument('--date', type=str, default=None, help="Date of email, YYYYMMDD format")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    else:
        args = parser.parse_args()
        main(args.qid, args.date) 

