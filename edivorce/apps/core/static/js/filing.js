$(window).ready(function () {
    function validateCourtFileNumber(e) {
        var rawText = $("#court-file-number").val();
        // remove all letters from the file number (e.g. 'VLC-S-E-20201124')
        let noLetters = rawText.replace(/[A-Za-z]/g, '');

        // make sure the format after removing all the letters is like this (e.g. '---20201124')
        let parts = noLetters.split('-');
        for (var i = 0; i < parts.length - 2; i++) {
            // if anything other than letters was found in the first parts of the number 
            // then display an error
            if (parts[0].length > 0) {
                $('#court-file-error').toggle(true);
                return false;
            }
        }
        
        // initial validation has passed.  Now remove everything except the numbers.
        let fileNumber = rawText.replace(/[^0-9]/g, '');
        const regex = RegExp('^[0-9]{4,10}$');
        // ensure that we are left with a 4-10 digit number
        var valid = !rawText || regex.test(fileNumber);
        if (valid) {
            // swap the value in the field to be the cleaned up number (e.g. '20201124')
            $("#court-file-number").val(fileNumber);
        }
        $('#court-file-error').toggle(!valid);
        if (valid && rawText !== fileNumber) {
            // if we rewrote the number, then fire another change event so it gets saved to the DB
            setTimeout(function(){ $("#court-file-number").trigger('change'); }, 100);
        }
        return valid;
    }

    $("#court-file-number").on('change', validateCourtFileNumber);
    validateCourtFileNumber();

    $('#submitDocuments').on('click', function (e) {
        var errors = []
        if (!validateCourtFileNumber()) {
            errors.push("A Court File Number contains only digits and must be between 4 and 10 digits in length");
        }
        $('div#app').children().each(function (i, child) {
            if ($(child).find("div.placeholder.required").length > 0) {
                var formName = $(child).find("h5 span > span").text();
                errors.push('Missing documents for ' + formName);
            }
        })
        var errorBox = $('#error-message-box');
        var messageList = $('#error-messages');
        if (errors.length > 0) {
            e.preventDefault();
            messageList.empty();
            errors.forEach(function (message) {
                messageList.append('<li>' + message + '</li>');
            });
            errorBox.show();
            window.scrollTo(0, 0);
        } else {
            errorBox.hide();
            // show the spinner overlay
            $('div#progress-overlay').show();
            $('div#progress-overlay-message').show();
            $('div#progress-overlay-spinner').spin('xlarge');            
        }
    });
});
