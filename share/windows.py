import win32print


def get_printers_name():
    return [i['pPrinterName'] for i in win32print.EnumPrinters(4 | 2, None, 5) if 'pPrinterName' in i]