def sum_numbers(ussd_request):
    return int(ussd_request.session['first_number']) + \
           int(ussd_request.session['second_number'])
