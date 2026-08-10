use std::rc::Rc;
use std::cell::RefCell;

pub struct CPUMemoryMap {
    pub ppu: ::ppu::PPU,
    pub ram: Box<[u8]>,
    // input
    pub cart: Rc<RefCell<::cartridge::Cartridge>>,
    pub controller1: RefCell<::controller::Controller>,
    pub controller2: RefCell<::controller::Controller>,
}

pub struct PPUMemoryMap {
    pub vram: Box<[u8]>,
    pub cart: Rc<RefCell<::cartridge::Cartridge>>,
    pub palettes: Box<[u8]>
}

// For now I'm just gonna assume NROM-128 because I'm just focusing on Donkey Kong
impl CPUMemoryMap {
    pub fn new(cart: Rc<RefCell<::cartridge::Cartridge>>, ppu: ::ppu::PPU) -> CPUMemoryMap {
        CPUMemoryMap{ram: Box::new([0; 0x800]),
                     cart: cart,
                     ppu: ppu,
                     controller1: RefCell::new(::controller::Controller::new(true)),
                     controller2: RefCell::new(::controller::Controller::new(false)),
                    }
    }

    pub fn read(&self, address: u16) -> u8 {
        match address {
            // 2k of ram repeated 4 times
            0 ... 0x1fff => {
                let data = self.ram[address as usize % 0x800];
                //println!("Read {:x} from {:x}", data, address as usize % 0x800);

                data
            },

            0x2000 ... 0x3fff => {
                let modaddr = address % 8;
                //println!("Read from PPU register: {}", modaddr);
                match modaddr {
                    0 => self.ppu.read_control_1(),
                    1 => self.ppu.read_control_2(),
                    2 => self.ppu.read_status(),
                    3 => self.ppu.read_oamaddr(),
                    4 => self.ppu.read_oamdata(),
                    5 => self.ppu.read_scroll_offset(),
                    6 => self.ppu.read_addr_offset(),
                    7 => self.ppu.read_ppudata(),
                    _ => panic!("Mod 8 cannot return anything greater than 7 but somehow it did")
                }
            },

            0x4000 => { panic!("Read from 0x4000") },
            0x4001 => { panic!("Read from 0x4001") },
            0x4002 => { panic!("Read from 0x4002") },
            0x4003 => { panic!("Read from 0x4003") },
            0x4004 => { panic!("Read from 0x4004") },
            0x4005 => { panic!("Read from 0x4005") },
            0x4006 => { panic!("Read from 0x4006") },
            0x4007 => { panic!("Read from 0x4007") },
            0x4008 => { panic!("Read from 0x4008") },
            0x4009 => { panic!("Read from 0x4009") },
            0x4010 => { panic!("Read from 0x4010") },
            0x4011 => { panic!("Read from 0x4011") },
            0x4012 => { panic!("Read from 0x4012") },
            0x4013 => { panic!("Read from 0x4013") },
            0x4014 => { panic!("Read from 0x4014") },
            0x4015 => { panic!("Read from 0x4015") },

            // Controller ports
            0x4016 => {
                self.controller1.borrow_mut().read()
            },
            0x4017 => {
                self.controller2.borrow_mut().read()
            },


            0x4018 ... 0x401F => {
                panic!("0x4018 ... 0x401F");
            },

            // PRG-RAM
            0x6000 ... 0x7FFF => {
                panic!("PRG-RAM");
            },

            // First 16k of ROM
            0x8000 ... 0xBFFF => {
                let cart = self.cart.borrow();
                cart.prgrom[address as usize - 0x8000]
            }

            // Last 16k of ROM (just a mirror for NROM-128)
            0xC000 ... 0xFFFF => {
                // REMEMBER THIS IS A MIRROR OF THE PREVIOUS BECAUSE NROM 128
                let cart = self.cart.borrow();
                cart.prgrom[address as usize - 0xC000]
            }
            _ => 0
        }
    }

    pub fn read16(&self, address: u16) -> u16 {
            let lo = self.read(address) as u16;
            let hi = self.read(address + 1) as u16;
            hi << 8 | lo
    }

    pub fn write(&mut self, data: u8, address: u16) {
        match address {
            // 2k of ram repeated 4 times
            0 ... 0x1fff => {
                //println!("Writing {} at {}", data, address);
                self.ram[address as usize % 0x800] = data;
                //println!("Wrote {:x} at {:x}", self.ram[address as usize % 0x800], address as usize % 0x800);
            },

            0x2000 ... 0x3fff => {
                let modaddr = address % 8;
                //println!("Write to PPU register: {}", modaddr);
                match modaddr {
                    0 => self.ppu.write_control_1(data),
                    1 => self.ppu.write_control_2(data),
                    2 => self.ppu.write_status(data),
                    3 => self.ppu.write_oamaddr(data),
                    4 => self.ppu.write_oamdata(data),
                    5 => self.ppu.write_scroll_offset(data),
                    6 => self.ppu.write_addr_offset(data),
                    7 => self.ppu.write_ppudata(data),
                    _ => panic!("Mod 8 cannot return anything greater than 7 but somehow it did")
                }
            },

            0x4000 => {},
            0x4001 => {},
            0x4002 => {},
            0x4003 => {},
            0x4004 => {},
            0x4005 => {},
            0x4006 => {},
            0x4007 => {},
            0x4008 => {},
            0x4009 => {},
            0x400a => {},
            0x400b => {},
            0x400c => {},
            0x400d => {},
            0x400e => {},
            0x400f => {},
            0x4010 => {},
            0x4011 => {},
            0x4012 => {},
            0x4013 => {},
            0x4014 => {
                let addr:u16 = ((data as u16) << 8);
                for i in 0..256 {
                    self.ppu.oam[i] = self.read(addr + (i as u16));
                }
            },
            0x4015 => {},

            // Controller ports
            0x4016 => {
                self.controller1.borrow_mut().write(data);
                if self.controller1.borrow().strobe {
                    self.controller2.borrow_mut().strobe = true;
                    self.controller2.borrow_mut().index = 0;
                } else {
                    self.controller2.borrow_mut().strobe = false;
                }
            },
            0x4017 => {
                self.controller2.borrow_mut().write(data)
            },

            0x4018 ... 0x401F => {
                panic!("0x4018 ... 0x401F");
            },

            // PRG-RAM
            0x6000 ... 0x7FFF => {
                panic!("PRG-RAM");
            },

            // First 16k of ROM
            0x8000 ... 0xBFFF => {
                panic!("Attempt to write to ROM");
            }

            // Last 16k of ROM (just a mirror for NROM-128)
            0xC000 ... 0xFFFF => {
                // REMEMBER THIS IS A MIRROR OF THE PREVIOUS BECAUSE NROM 128
                panic!("Attempt to write to ROM");
            }
            _ => panic!("Write to an address outside of CPU memory range")
        }
    }
}

impl PPUMemoryMap {
    pub fn new(cart: Rc<RefCell<::cartridge::Cartridge>>) -> PPUMemoryMap {
        PPUMemoryMap{vram: Box::new([0xFF; 0x800]) , cart: cart, palettes: Box::new([0; 0x800])}
    }

    pub fn read(&self, address: u16) -> u8 {
        match address {
            0 ... 0x1FFF => {
                let cart = self.cart.borrow();
                cart.chrrom[(address) as usize]
            },

            0x2000 ... 0x3EFF => {
                self.vram[address as usize % 0x800]
            }

            0x3F00 ... 0x3FFF => {
                self.palettes[address as usize % 0x20]
            }
            _ => panic!("Read from outside of PPU memory")
        }
    }

    pub fn write(&mut self, data: u8, address: u16) {
        match address {
            0 ... 0x1FFF => {
                panic!("Attempt to write to ROM");
            },

            0x2000 ... 0x3EFF => {
                self.vram[address as usize % 0x800] = data;
            }

            0x3F00 ... 0x3FFF => {
                self.palettes[address as usize % 0x20] = data;
            }
            _ => {
                println!("{:x}", address);
                panic!("Read from outside of PPU memory");
            }
        }
    }
}
