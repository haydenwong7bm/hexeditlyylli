import os
import struct

from colorama import init, Fore, Back, Style

import hexeditlyylli.edit as edit
import hexeditlyylli.inspect as inspect

init()

discard_negatives = lambda x: x if x >= 0 else 0

def option_parser(file, opt):
    opt = opt.split(' ', maxsplit=1)
    
    if opt[0] == 'inspect':
        opt = [opt[0]] + opt[1].split(' ', maxsplit=5)
    elif opt[0] in {'help', 'exit', 'next', 'prev', ''}:
        pass
    else:
        opt = [opt[0]] + opt[1].split(' ', maxsplit=1)
    
    if opt[0] == 'write':
        file.write(int(opt[1], 16), opt[2])
    elif opt[0] == 'append':
        file.append(opt[1])
    elif opt[0] == 'insert':
        file.insert(int(opt[1], 16), opt[2])
    elif opt[0] == 'remove':
        file.remove(int(opt[1], 16), int(opt[2], 16))
    elif opt[0] == 'trunc' or opt[0] == 'truncate':
        file.truncate(int(opt[1], 16))
    elif opt[0] == 'inspect':
        if opt[1] == 'view':
            file.inspect_view(opt[2], int(opt[3], 16))
        elif opt[1] == 'edit':
            file.inspect_edit(opt[2], int(opt[3], 16), opt[4], opt[5])   
        else:
            raise ValueError(f"invaild option: '{opt[0]} {opt[1]}'")
    elif opt[0] == 'goto':
        file.goto(int(opt[1], 16))
    elif opt[0] == 'help':
        raise NotImplementedError('work in progress')
    elif opt[0] == 'exit':
        exit()
    elif opt[0] == 'next':
        if len(opt) == 1:
            file.next(1)
        else:
            file.next(opt[1])
    elif opt[0] == '':
        file.next()
    elif opt[0] == 'prev':
        if len(opt) == 1:
            file.prev(1)
        else:
            file.prev(opt[1])
    else:
        raise ValueError(f"invaild option: '{opt[0]}'")
        
    return opt[0]

def code_to_char(code, highlight=None):
    if 0x00 <= code <= 0x1f or code in {0x81, 0x8d, 0x8f, 0x90, 0x9d}:
        returned = f'{Fore.GREEN}.{Style.RESET_ALL}'
    elif code == 0x7f:
        returned = f'{Fore.GREEN}\u2302{Style.RESET_ALL}'
    else:
        returned = struct.unpack("cc", code.to_bytes(2, 'big'))[1].decode('windows-1252')
        
    if highlight != None:
        returned = f'{highlight[0]}{highlight[1]}{returned}'
    
    return returned

class HexFile(object):
    def __init__(self, file, bytes_per_line, line_size):
        self.file = file
        self.name = file.name
        self.bytes_per_line = bytes_per_line
        self.line_size = line_size
        self.byte_size = self.line_size * self.bytes_per_line
        
        self.__half = bytes_per_line // 2
    
    def print(self, start=None, end=None, inspect=None):
        if start != None:
            highlight_flag = True
            if inspect:
                highlight_back = Back.YELLOW
            else:
                highlight_back = Back.WHITE
            highlight_fore = Fore.BLACK
        else:
            highlight_flag = False
        
        line_no = self.file.tell() // self.byte_size * self.byte_size
        
        filesize = os.path.getsize(self.file.name)
        
        foo = len(f'{filesize - 1:x}')
        if foo == 1:
            foo = 2
        
        break_flag = False
        
        print(f'{"-" * foo}-.{"-" * self.__half * 3}-.{"-" * self.__half * 3}-..-{"-" * self.bytes_per_line}')
        
        for line_section_no in range(0, self.byte_size, self.bytes_per_line):
            contents = self.file.read(self.bytes_per_line)
            contents = bytes(contents)
            
            printed = ''
            
            if contents == b'':
                if start != None:
                    printed = f'{printed}{Style.RESET_ALL}'
                
                if filesize == 0 and not break_flag:
                    break_flag = True
                else:
                    break
            
            printed = f'{line_no + line_section_no:0{foo}x} | '
            
            byte_pos = -1
            
            for byte_pos, byte in enumerate(contents):
                current_byte_pos = line_no + line_section_no + byte_pos
                
                if highlight_flag:
                    if current_byte_pos == start or (start <= current_byte_pos <= end and byte_pos == 0):
                        printed = f'{printed}{highlight_back}{Fore.BLACK}'
                
                printed = f'{printed}{byte:02x} '
                
                if highlight_flag:
                    if byte_pos == self.bytes_per_line - 1:
                        printed = f'{printed[:-1]}{Style.RESET_ALL} '
                    if current_byte_pos == end:
                        printed = f'{printed[:-1]}{Style.RESET_ALL} '
                
                if byte_pos == self.__half - 1:
                    if highlight_flag:
                        if start <= current_byte_pos < end:
                            printed = f'{printed[:-1]}{Style.RESET_ALL} | {highlight_back}{Fore.BLACK}'
                        else:
                            printed = f'{printed}| '
                    else:
                        printed = f'{printed}| '
            
            if byte_pos < self.bytes_per_line - 1:
                for i in range(byte_pos + 1, self.bytes_per_line):
                    printed = f'{printed}   '
                    
                    if i == self.__half - 1:
                        printed = f'{printed}| '
            
            printed = f'{printed}|| '
            
            for byte_pos, byte in enumerate(contents):
                current_byte_pos = line_no + line_section_no + byte_pos
                
                if highlight_flag:
                    if start <= current_byte_pos <= end:
                        printed = f'{printed}{code_to_char(byte, (highlight_back, highlight_fore))}'
                    else:
                        printed = f'{printed}{Style.RESET_ALL}{code_to_char(byte)}'
                else:
                    printed = f'{printed}{code_to_char(byte)}'
            
            if highlight_flag:
                printed = f'{printed}{Style.RESET_ALL}'
            
            print(printed)
            
        print(f'{"-" * foo}-\'{"-" * self.__half * 3}-\'{"-" * self.__half * 3}-\'\'-{"-" * self.bytes_per_line}')
    
    def next(self, pages=1):
        self.file.seek((self.file.tell() // self.byte_size + pages - 1) * self.byte_size)
        
        if self.file.tell() >= os.path.getsize(self.file.name):
            exit()
        
        self.print()
    
    def prev(self, pages=1):
        self.file.seek(discard_negatives((self.file.tell() // self.byte_size - pages - 1) * self.byte_size))
        
        self.print()
    
    def goto(self, pos):
        self.file.seek(pos // self.byte_size * self.byte_size)
        self.print()
    
    def close(self):
        self.file.close()
    
    def inspect_view(self, endian, pos):
        self.file.seek(discard_negatives((self.file.tell() // self.byte_size - 1) * self.byte_size))
        self.print(pos, 8, True)
        
        print()
        
        inspected = inspect.inspect(self.file, pos, endian)
        
        printed_foo = "-" * 23
        printed_bar = "-" * 29
        
        print(f'{printed_bar}.{printed_foo}.{printed_foo}\n{"Type":<29}|{"Unsigned":^23}|{"Signed":^23}\n{printed_bar}+{printed_foo}+{printed_foo}')
        
        for type_, inspected_item in inspected[0].items():
            print(f'{type_:<29}| {inspected_item[0]:< 21} | {inspected_item[1]:< 21} ')
        
        print(f"{printed_bar}+{printed_foo}'{printed_foo}")
        
        for type_, inspected_item in inspected[1].items():
            print(f'{type_:<29}| {inspected_item:< 45}')
        
        print(f"{printed_bar}'{printed_foo}-{printed_foo}")
    
    def inspect_edit(self, endian, pos, dtype, data):
        data_ = edit.write_typed_data(self.file, endian, pos, dtype, data)    
        self.print(pos, len(data_))
    
    def write(self, start, data):
        if data[0] == '"' or data[0] == "'":
            data = data[1:-1]
            edit.write_ascii(self.file, start, data)
        else:
            data = bytes([int(data[i:i+2], 16) for i in range(0, len(data), 2)])
            edit.write_bytes(self.file, start, data)
        
        self.file.seek(start // self.byte_size * self.byte_size)
        
        end = start + len(data) - 1
        self.print(start, end)
    
    def insert(self, start, data, chunk_size=1024):
        if data[0] == '"' or data[0] == "'":
            data = data[1:-1]
            self.file = edit.insert_ascii(self.file, start, data, chunk_size)
        else:
            data = bytes([int(data[i:i+2], 16) for i in range(0, len(data), 2)])
            self.file = edit.insert_bytes(self.file, start, data, chunk_size)
        
        self.file.seek(start // self.byte_size * self.byte_size)
        
        end = start + len(data) - 1
        self.print(start, end)
    
    def remove(self, start, end, chunk_size=1024):
        self.file = edit.remove(self.file, start, end, chunk_size)
        
        self.file.seek(start // self.byte_size * self.byte_size)
        
        self.print()
    
    def append(self, data):
        start = os.path.getsize(self.file.name)
        
        self.write(start, data)
        
        end = os.path.getsize(self.file.name)
        
        self.print(start, end)
    
    def truncate(self, size):
        orinigal_pos = self.file.tell()
        
        edit.truncate(self.file, size)
        
        size_ = os.path.getsize(self.file.name)
        if orinigal_pos >= size_:
            self.file.seek(discard_negatives(size_ - self.byte_size))
        
        self.print()

def main(filename, bytes_per_line, line_size):
    with open(filename, 'rb+') as f:
        file = HexFile(f, bytes_per_line, line_size)
        
        filesize = os.path.getsize(file.name)
        
        file.print()
        
        break_flag = False
        while file.file.tell() < filesize or filesize == 0:
            if filesize == 0:
                break_flag = True
            
            option = input('Option command (Press Enter to continue): ')
            option = option_parser(file, option)
            
            filesize = os.path.getsize(file.name)
            
            if filesize == 0 and break_flag:
                break