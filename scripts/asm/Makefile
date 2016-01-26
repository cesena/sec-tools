PORT=5556


# {{{ High level.

r2: build
	@echo "--> Debugging with Radare2: '${NAME}.elf'"
	@r2 -d ./${NAME}.elf ${ARGS}

gdb: build
	@echo "--> Debugging with GDB: '${NAME}.elf'"
	@gdb ./${NAME}.elf

all: build
	@echo "--> Running '${NAME}.elf'"
	@./${NAME}.elf

client: hex client_run clean

client_run:
	@echo ""
	@echo "----- STARTING CLIENT (Name: ${NAME}, Port: ${PORT}) -----"
	@python client.py ${NAME} | nc localhost ${PORT}
	@echo "----- ENDING CLIENT -----"
	@echo ""

server: clean
	@echo "--> Rebuilding and Starting server at port '${PORT}'"
	@gcc level18.c -o level18.elf
	@./level18.elf ${PORT}
	@make clean NAME=level18

# }}}

# {{{ Low level.

build: preprocess
	@echo "--> Generating 'elf' file for '${NAME}.gen.s'"
	@nasm -felf ${NAME}.gen.s -o ${NAME}.o
	@ld -melf_i386 ${NAME}.o -o ${NAME}.elf

hex: preprocess
	@echo "--> Generating 'hex' and 'raw' files for '${NAME}.gen.s'"
	@nasm ${NAME}.gen.s -o ${NAME}.raw
	@od -tx1 -An -v -w1000 ${NAME}.raw |sed "s/ /\\\\\x/g" > ${NAME}.hex
	@cat ${NAME}.hex | grep -o 'x' | wc -l

preprocess: clean
	@echo "--> Preprocessing input assembly file: '${NAME}.s'. Writing to: '${NAME}.gen.s'"
	@ruby -e 'require "erb"; File.write("${NAME}.gen.s", ERB.new(File.read("${NAME}.s")).result)'

clean:
	@echo "--> Removing dirty files for '${NAME}'"
	-@rm ${NAME}.{gen.s,elf,o,raw,hex} 2&> /dev/null

# }}}
