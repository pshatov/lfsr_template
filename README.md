Very easy to use Verilog LFSR generator
=======================================

Need a quick and dirty RNG for your FPGA project, but that page you bookmarked to look up maximal length polynomials went down once again?

Don't want to spend time converting 1-based hexadecimal powers notation to 0-based decimal and still mess up all the bit indices in the end?

Guess what, there's a solution!

---

**WARNING**: LFSR-based random number generators are easily predictable, especially when their internal state is small. They are perfectly suitable for things where security is not of concern. For example, generation of noise for image dithering or simulating random memory accesses. If you're working on a crypto-related design, never use an LFSR as-is and better think twice about what you're doing.

---



How to generate an LFSR
-----------------------

The easiest way is to just specify the desired bit width, say, eight:

```text
$ python lfse_template.py 8
```

This will automatically pick a random polynomial and generate the module `lfsr_8.v` and the corresponding testbench called `tb_lfsr_8.v`

Note, that you can fine tune certain options, use `-h` for more information. The following will generate an 8-bit register called `foo.v` based on polynomial `x^8 + x^7 + x^2 + x + 1` with the starting value of `123`.

```text
$ python lfsr_template.py --init-value 0x7B --poly 0xC3 --module-name foo 8
```

How to run simulation with Icarus & GTKWave
-------------------------------------------

1. Assuming you already generated an 8-bit module with the default name, compile the testbench first (you must compile both the module and the testbench, Icarus should be smart enough to determine the top module itself):

    ```text
    $ iverilog -o tb_lfsr_8.vvp lfsr_8.v tb_lfsr_8.v
    ```

2. Run the simulation, you should see something like this. The testbench will check, that the LFSR reverts to the initial value after full period:

	```text
	$ vvp tb_lfsr_8.vvp
	VCD info: dumpfile tb_lfsr_8.vcd opened for output.
	Output value after full period matches the initial value - OK
	tb_lfsr_8.v:50: $finish called at 4550000 (1ps)
	```

3. You can use GTKWave in case you want to inspect the simulation dump:

	```text
	$ gtkwave tb_lfsr_8.vcd
	```

Please note, that Galois-style feedback is not yet supported, please use the default Fibonacci-style.

