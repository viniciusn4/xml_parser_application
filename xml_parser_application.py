import os
import zipfile

from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from bs4 import BeautifulSoup

window = Tk()
window.title('CVAT - Resultado do Lote | Versão: 1.2')
window.configure(background='#f0f2f5')
window.geometry('700x700')
window.resizable(True, True)


def extract_zip(zip_path):
    """Extract XML file from a Zip.

    Parameters
    ----------
    zip_path : string
        Zip file path.

    Returns
    -------
    string
        Path to the extracted file.
    """
    zip_folder = os.path.dirname(zip_path)
    extracted_path = os.path.join(zip_folder, os.path.basename(zip_path).split('_')[1] + '.xml')
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(zip_folder)
    if os.path.isfile(extracted_path) is False:
        os.rename(os.path.join(zip_folder, 'annotations.xml'), extracted_path)
    else:
        os.remove(extracted_path)
        os.rename(os.path.join(zip_folder, 'annotations.xml'), extracted_path)
    return extracted_path


def file_browser(entry_path):
    """File browser to select an XML or a Zip and show the path on the Entry widget.

    -------
    """
    filename = filedialog.askopenfilename(initialdir=os.getcwd(), title='Selecione um arquivo', filetypes=((
        'Arquivo ZIP', '*.zip*'), ('Arquivo XML', '*.xml*'), ('Todos os arquivos', '*.*')))

    entry_path.delete(0, END)
    entry_path.insert(0, filename)


def save_content(file_path, batch_name, label, content, repeated_label):
    """Save the content into a file.

    Parameters
    ----------
    file_path : string
        Path to the file where the content is saved.
    batch_name : string
        Name of the batch read from XML.
    label : String
        Name of the label in the XML file.
    content : collection
        List containing all the same label from BeautifulSoup findall() method.
    repeated_label : list
        List to add all IDs.
    """
    index_list = []
    save_file = os.path.dirname(file_path)
    with open(f'{os.path.join(save_file, label)}_{batch_name}.txt', 'w') as txt:
        for tag in content:
            get_index = tag.parent.get('id')
            index_list.append(int(get_index))
            repeated_label.append(get_index)  # TODO: repeated_label contém todos os IDs com anotação, mesmo duplicados.
        index_list.sort()
        for index in index_list:
            txt.write(f'{label} - {index}\n')
# TODO: Alterar repeated_label para all_id, faz mais sentido, dá pra usar no empty também.
    return len(index_list)


def show_text(dictionary, label_dict):
    """Show formatted output in text widget.

    Parameters
    ----------
    dictionary : dict
        Dictionary containing the data to be formatted and displayed in text widget.
    label_dict : dict
        Dictionary containing each kind of label that exist in XML file.
    """
    raw_label = 'Dado "raw":\n'
    text_output.insert(END, raw_label)

    keys_in_line = 'nome_do_lote;id_do_lote;id_da_anotação'
    for k, v in label_dict.items():
        keys_in_line += f';{k}'
    text_output.insert(END, keys_in_line)

    values_in_line = f"\n{dictionary['batch_name']};{dictionary['batch_id']};{dictionary['job_id']}"
    for k, v in label_dict.items():
        values_in_line += f';{v}'
    text_output.insert(END, values_in_line)

    text_top = f'''
\n---
>>> Nome do Lote: {dictionary['batch_name']}
>>> ID do Lote: {dictionary['batch_id']}
>>> ID da Anotação: {dictionary['job_id']}\n
'''
    text_output.insert(END, text_top)

    for k, v in label_dict.items():
        text_body = f'{k.title()}: {v}.\n'
        text_output.insert(END, text_body)

    text_bottom = f'''
Há {dictionary['repeated']} imagens com label repetida: {dictionary['repeated_list']}\n
Há {dictionary['empty']} imagens sem label: {dictionary['empty_list']}
\nRegistros salvos em: {dictionary['extracted_path']}.
{127 * '-'}\n
'''
    text_output.insert(END, text_bottom)


def read_file():
    """Read CVAT output XML.

    ...
    """
    repeated_label = []
    repeated_list = []
    empty_list = []
    all_image_id = []
    all_tag_id = []

    file_path = path.get()
    if not os.path.isfile(file_path):
        messagebox.showinfo('Falha!', 'Arquivo não encontrado.')
    elif file_path.endswith('.zip'):
        extracted_path = extract_zip(file_path)
        with open(extracted_path, 'r') as xml:
            data = xml.read()
    elif file_path.endswith('.xml'):
        with open(file_path, 'r') as xml:
            data = xml.read()
    else:
        messagebox.showerror('Erro!', 'Arquivo inválido.')

    bs_data = BeautifulSoup(data, 'xml')
    batch_id = bs_data.find('id').get_text()
    batch_name = bs_data.find('name').get_text()
    segment = bs_data.find('segment')
    job_id = segment.find('id').get_text()
    all_image = bs_data.find_all('image')
    all_tag = bs_data.find_all('tag')
    find_labels = bs_data.find('labels')
    labels_name = find_labels.find_all('name')
    labels_list = [label.get_text() for label in labels_name]

    text_body_dict = {}
    for label in labels_list:
        content = bs_data.find_all('tag', {'label': label})
        index_len_list = save_content(file_path, batch_name, label, content, repeated_label)
        text_body_dict[label] = index_len_list

    # Repeated labels:
    for i in repeated_label:
        if repeated_label.count(i) > 1:
            repeated_list.append(int(i))
            while repeated_label.count(i) > 1:
                index = repeated_label.index(i)
                repeated_label.pop(index)
    repeated_list.sort()

    # Empty labels:
    for tag in all_tag:
        all_tag_id.append(tag.parent.get('id'))
    for image in all_image:
        image_id = image.get('id')
        all_image_id.append(image.get('id'))
        if image_id not in all_tag_id:
            empty_list.append(int(image_id))
    empty_list.sort()

    dict_content = {
        'batch_name': batch_name,
        'batch_id': batch_id,
        'job_id': job_id,
        'repeated': len(repeated_list),
        'repeated_list': repeated_list,
        'empty': len(empty_list),
        'empty_list': empty_list,
        'extracted_path': os.path.dirname(file_path)
    }

    show_text(dict_content, text_body_dict)

    repeated_label.clear()
    repeated_list.clear()
    empty_list.clear()
    all_image_id.clear()
    all_tag_id.clear()


# Label 'Caminho'
lb_path = Label(window, text='Caminho:', bg='#f0f2f5', font=('arial', 11, 'bold'))
lb_path.place(relx=0.03, rely=0.03)

# Entry 'Caminho'
path = StringVar()
entry_path = Entry(window, textvariable=path, font=('arial', 11))
entry_path.place(relx=0.03, rely=0.07, relwidth=0.94)
entry_path.focus_set()

# Button 'Importar'
bt_browser_file = Button(window, text='Importar', bd=2, bg='#5a5a5a', fg='white', font=('arial', 11, 'bold'),
                         command=lambda: file_browser(entry_path))
bt_browser_file.place(relx=0.03, rely=0.12, relwidth=0.11, relheight=0.06)

# Button 'Executar'
bt_run = Button(window, text='Executar', bd=2, bg='#1890ff', fg='white', font=('arial', 11, 'bold'), command=read_file)
bt_run.place(relx=0.445, rely=0.12, relwidth=0.11, relheight=0.06)

# Label 'Saída'
lb_output = Label(window, text='Saída:', bg='#f0f2f5', font=('arial', 11, 'bold'))
lb_output.place(relx=0.03, rely=0.22)

# Scrollbar of the Text
scrollbar = Scrollbar(window, bg='#7e8182', activebackground='#5a5a5a')
scrollbar.place(relx=0.945, rely=0.26, relwidth=0.025, relheight=0.72)

# Text output data
text_output = Text(window, bg='#ffffff', yscroll=scrollbar.set, font=('arial', 11))
text_output.place(relx=0.03, rely=0.26, relwidth=0.915, relheight=0.72)
scrollbar.config(command=text_output.yview)

window.mainloop()
