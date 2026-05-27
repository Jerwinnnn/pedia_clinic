import smtplib

username = 'tugasjerwin7@gmail.com'
password = 'lufa sqdo xgao ithb'
to_email = 'tugasjerwin7@gmail.com'

try:
    with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as s:
        s.ehlo()
        s.starttls()
        s.login(username, password)
        s.sendmail(username, to_email, 'Subject: Test\n\nIt works!')
    print('SUCCESS - check your inbox!')
except Exception as e:
    print(f'FAILED: {e}')