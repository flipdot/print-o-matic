# print-o-matic
Fill out any PDF you want, automated!


# Prerequisites
Install the needed Python 3 packages:
```bash
pip3 install reportlab PyPDF2
```

# Single document
To only fill one form, use the following command:
```bash
./fill-form.py geldzuwendung name="Max Mustermann" street="Musterstraße 123" city="12345 Musterstadt" date="31.12.2020" amount="42.23"
```

This will fill in the document configured in `config/geldzuwendung` for Max Mustermann at the given address and date. The spenden amount translates to 42,23€. _Do not omit the double ticks._


# Batch creation
For filling out multiple documents, fill in the file `csv/geldzuwendung.csv` and afterwards use the bundled shell script like so:
```bash
./batch.sh
```
This will create a directory called `output` inside the working directory, where you will find all the created documents.


# Batch printing
To print all the documents with the default printer use the following command:
```bash
lpr output/*.pdf
```

This requires CUPS to be installed. If you get an error about no default printer being set, please consult [this help page](https://www.cups.org/documentation.php/options.html#DEFAULT).


# Custom documents
Have a look at the `config` directory. The files within should speak for themselves enough to let you create your own configs.

