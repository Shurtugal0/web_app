import os
import json
from tqdm import tqdm
import streamlit as st
import pdfplumber
import io

total = ['Итого', 'Сумма', 'Всего к оплате', 'Цена']
invoice_num = ['Счет', 'Счёт', 'СЧЕТ', 'СЧЁТ']
date = ['Дата']
agent = ['Продавец', 'Исполнитель', 'Получатель платежа', 'Получатель',
         'Продавец:', 'Исполнитель:','Получатель платежа:', 'Получатель:']
super_agent = ['Поставщик', 'Поставщик:']
quotes = ['“', '”', '‘', '’', '«', '»', '„', '“', '„', '”', '»', '«', '"']

def is_number(n):
    try:
        float(n)
    except ValueError:
        return False
    return True

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)

def ocr_core(pdf_file):
    pdf = pdfplumber.open(pdf_file)
    first_page = pdf.pages[0]
    image = first_page.to_image()
    image = image.draw_rects(first_page.extract_words())
    text = first_page.extract_text()
    return image.annotated, [text]

def process_text(texts):
    sum_cand = []
    invoice_num_cand = []
    date_cand = []
    agent_cand = []
    get_agent_name = False

    
    for text in texts:
        text = text.split('\n')
        pruned_text = []
        for elt in text:
            if elt != '' and elt != ' ':
                pruned_text.append(elt)
                
        if any(x in quotes for x in pruned_text[0]):
            agent_cand.append(pruned_text[0])
        for row in pruned_text:
            if get_agent_name:
                agent_cand.append(row)
                get_agent_name = False
            if not agent_cand:
                for word in agent:
                    if word in row.split(' '):
                        line = row.split(' ')
                        if len(line) < 2:
                            get_agent_name = True
                        else:
                            agent_cand.append(' '.join(line[1:]))
                            
            for word in super_agent:
                if word in row.split(' '):
                    line = row.split(' ')
                    agent_cand = [' '.join(line[1:])]
            
            for word in total:
                if word in row:
                    if has_numbers(row):
                        number = ''
                        for elt in row.split(' '):
                            elt = elt.replace(',', '.')
                            if is_number(elt):
                                number += elt
                            if '.' in number:
                                break
                            if number != '':
                                if '.' in elt:
                                    number += elt
                        if number != '':
                            sum_cand.append(float(number))
                        
            if not invoice_num_cand:
                for word in invoice_num:
                    if word in row:
                        if has_numbers(row):
                            line = row.split(' ')
                            if 'от' in line:
                                invoice_num_cand.append(line[line.index('от') - 1])
                                date_cand.append(' '.join(line[line.index('от') + 1:]))
                            else:
                                invoice_num_cand.append(line[-1])
                        
            if not date_cand:
                for word in date:
                    if word in row:
                        line = row.split(' ')
                        date_cand.append(' '.join(line[1:]))

    return max(sum_cand), agent_cand, date_cand, invoice_num_cand


def main():

    st.title("Invoice OCR demo")
    file_up = st.file_uploader("Upload a document", type="pdf")

    if file_up:
        pdf = io.BytesIO(file_up.read())
        image, text = ocr_core(pdf)
        fin_sum, fin_agent, fin_date, fin_invoice_num = process_text(text)

        res = {}
        res['total'] = [fin_sum]
        res['agent_name'] = fin_agent
        res['date'] = fin_date
        res['invoice_number'] = fin_invoice_num

        st.image(image, caption='Recognized words', use_column_width=True)

        res_json = json.dumps(res, indent = 4, ensure_ascii=False)
        st.download_button('Download JSON', res_json, file_name='result.json')

if __name__ == '__main__':
    main()