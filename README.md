# spend-o-matic
Create spendenbescheinigungs on the fly!

# Prerequisites
Install the needed Python 3 packages:
```bash
pip3 install reportlab PyPDF2
```

# Single document
To create only one spendenbescheinigung, use the following command:
```bash
python spende.py "Max Mustermann" "Musterstraße 123" "12345 Musterstadt" "4223" "2020-12-31"
```

This will create a spendenbescheinigung for Max Mustermann at the given address and date. The spenden amount translates to 42,23€.

# Batch creation
For the creation of multiple spendenbescheinigungs, fill in the file `spender.csv` and afterwards use the bundled shell script like so:
```bash
./create-forms.sh
```
This will create a directory called `pdf` inside the working directory, where you will find all the created spendenbescheinigungs.

# Batch printing
To print all the documents with the default printer use the following command:
```bash
lpr pdf/*
```

This requires CUPS to be installed. If you get an error about no default printer being set, please consult [this help page](https://www.cups.org/documentation.php/options.html#DEFAULT).

