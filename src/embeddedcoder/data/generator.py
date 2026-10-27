"""
Comprehensive multi-domain dataset generator for Universal Embedded Systems Engineering.
Generates rich, technically accurate training examples across all 9 taxonomy domains.
"""

from typing import List, Dict, Any
from embeddedcoder.core.constants import (
    Subdomain, Architecture, HardwarePlatform, VerificationMethod
)
from embeddedcoder.protocols.crc import crc16_modbus, nmea_checksum
from embeddedcoder.protocols.modbus import ModbusRTU
from embeddedcoder.protocols.can import CANFrame
from embeddedcoder.protocols.telematics import AIS140Packet


class EmbeddedDataGenerator:
    """Generates structured, verified training examples across the 9 subdomains."""

    @classmethod
    def generate_all(cls) -> List[Dict[str, Any]]:
        dataset: List[Dict[str, Any]] = []
        dataset.extend(cls._generate_c_cpp_examples())
        dataset.extend(cls._generate_mcus_socs_examples())
        dataset.extend(cls._generate_peripherals_examples())
        dataset.extend(cls._generate_rtos_examples())
        dataset.extend(cls._generate_linux_examples())
        dataset.extend(cls._generate_protocol_examples())
        dataset.extend(cls._generate_wireless_examples())
        dataset.extend(cls._generate_diagnostics_examples())
        dataset.extend(cls._generate_power_security_examples())
        return dataset

    @classmethod
    def _generate_c_cpp_examples(cls) -> List[Dict[str, Any]]:
        examples = []
        
        # 1. Lock-free SPSC Ring Buffer in C
        examples.append({
            "id": "EC-C-001",
            "subdomain": Subdomain.EMBEDDED_C_CPP.value,
            "platform": HardwarePlatform.UNIVERSAL.value,
            "architecture": Architecture.GENERIC.value,
            "language": "c",
            "difficulty": "advanced",
            "verification_method": VerificationMethod.GCC_COMPILATION.value,
            "instruction": "Implement a thread-safe, lock-free Single Producer Single Consumer (SPSC) circular byte ring buffer in C suitable for interrupt-driven UART reception without dynamic memory allocation.",
            "response": """Below is an interrupt-safe Single Producer Single Consumer (SPSC) circular byte ring buffer implemented in C99.

### Architecture & Concurrency Notes:
1. **Power-of-Two Sizing:** Masking (`index & (CAPACITY - 1)`) is used instead of expensive modulo division, which is critical for deterministic interrupt service routines.
2. **Volatile Head & Tail:** Marked `volatile` so the compiler emits memory reads/writes on every access rather than caching them in CPU registers.
3. **Memory Barrier:** On modern architectures (Cortex-M3/M4/M7, RISC-V), a data memory barrier (`__DMB()` or compiler barrier) ensures the data byte is committed to memory before the write index updates.

```c
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#define RING_BUFFER_SIZE 256  /* Must be a power of two */
#define RING_BUFFER_MASK (RING_BUFFER_SIZE - 1)

typedef struct {
    uint8_t buffer[RING_BUFFER_SIZE];
    volatile uint32_t head;  /* Written by producer (e.g. UART ISR) */
    volatile uint32_t tail;  /* Read by consumer (e.g. main loop) */
} ring_buffer_t;

void ring_buffer_init(ring_buffer_t *rb) {
    if (!rb) return;
    rb->head = 0;
    rb->tail = 0;
}

bool ring_buffer_push(ring_buffer_t *rb, uint8_t byte) {
    uint32_t next_head = (rb->head + 1) & RING_BUFFER_MASK;
    if (next_head == rb->tail) {
        return false; /* Buffer Full */
    }
    rb->buffer[rb->head] = byte;
    rb->head = next_head;
    return true;
}

bool ring_buffer_pop(ring_buffer_t *rb, uint8_t *byte) {
    if (rb->head == rb->tail) {
        return false; /* Buffer Empty */
    }
    *byte = rb->buffer[rb->tail];
    rb->tail = (rb->tail + 1) & RING_BUFFER_MASK;
    return true;
}

size_t ring_buffer_available(const ring_buffer_t *rb) {
    return (rb->head - rb->tail) & RING_BUFFER_MASK;
}
```""",
            "expected_output": "ring_buffer_t"
        })

        # 2. Bit manipulation and volatile hardware register abstraction
        examples.append({
            "id": "EC-C-002",
            "subdomain": Subdomain.EMBEDDED_C_CPP.value,
            "platform": HardwarePlatform.GENERIC_CORTEX_M.value,
            "architecture": Architecture.ARM_CORTEX_M.value,
            "language": "c",
            "difficulty": "intermediate",
            "verification_method": VerificationMethod.GCC_COMPILATION.value,
            "instruction": "Write portable C macros for robust bit manipulation and explain how to define volatile peripheral memory-mapped register pointers safely.",
            "response": """In embedded C, direct register manipulation requires careful typing and bitwise operations to avoid compiler optimizations that elide hardware accesses.

### 1. Robust Bit Manipulation Macros
```c
#include <stdint.h>

#define BIT(x)                 (1UL << (x))
#define BIT_SET(reg, bit)      ((reg) |= BIT(bit))
#define BIT_CLEAR(reg, bit)    ((reg) &= ~BIT(bit))
#define BIT_TOGGLE(reg, bit)   ((reg) ^= BIT(bit))
#define BIT_CHECK(reg, bit)    (((reg) & BIT(bit)) != 0)

#define BITS_SET_MASK(reg, mask, val) \\
    ((reg) = ((reg) & ~(mask)) | ((val) & (mask)))
```

### 2. Peripheral Register Pointer Abstraction
Always declare memory-mapped registers as `volatile uint32_t * const`:
```c
/* Base address of GPIO Port A on hypothetical Cortex-M */
#define GPIOA_BASE       (0x40020000UL)

/* Structure representing the register layout */
typedef struct {
    volatile uint32_t MODER;    /* Mode register, offset 0x00 */
    volatile uint32_t OTYPER;   /* Output type register, offset 0x04 */
    volatile uint32_t OSPEEDR;  /* Output speed register, offset 0x08 */
    volatile uint32_t PUPDR;    /* Pull-up/pull-down register, offset 0x0C */
    volatile uint32_t IDR;      /* Input data register, offset 0x10 */
    volatile uint32_t ODR;      /* Output data register, offset 0x14 */
    volatile uint32_t BSRR;     /* Bit set/reset register, offset 0x18 */
} GPIO_TypeDef;

#define GPIOA ((GPIO_TypeDef * const)GPIOA_BASE)

/* Usage */
void configure_pin5_output(void) {
    /* Set Pin 5 as General Purpose Output (Mode 01) */
    GPIOA->MODER &= ~(0x3UL << (5 * 2));
    GPIOA->MODER |=  (0x1UL << (5 * 2));
    
    /* Atomic Set Pin 5 High using BSRR */
    GPIOA->BSRR = BIT(5);
}
```

### Why `volatile` is mandatory:
Hardware registers can change asynchronously outside the compiler's knowledge (e.g. status flags set by hardware). Without `volatile`, the compiler may optimize polling loops into infinite loops:
```c
/* BAD without volatile: compiled to a single read and cached in register */
while ((UART->SR & UART_SR_TXE) == 0); 
```""",
            "expected_output": "GPIO_TypeDef"
        })

        # 3. Fixed-size Memory Block Allocator (Fragment-free)
        examples.append({
            "id": "EC-C-003",
            "subdomain": Subdomain.EMBEDDED_C_CPP.value,
            "platform": HardwarePlatform.UNIVERSAL.value,
            "architecture": Architecture.GENERIC.value,
            "language": "c",
            "difficulty": "advanced",
            "verification_method": VerificationMethod.GCC_COMPILATION.value,
            "instruction": "Implement a deterministic, zero-fragmentation fixed-size block memory pool allocator in C for embedded systems where dynamic heap allocation (malloc) is forbidden.",
            "response": """In safety-critical firmware, dynamic heap allocation (`malloc`/`free`) causes nondeterministic execution times and catastrophic heap fragmentation. A **Fixed-Size Block Pool Allocator** provides O(1) allocation and deallocation with zero external fragmentation.

```c
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#define POOL_BLOCK_SIZE  64
#define POOL_BLOCK_COUNT 16

typedef struct BlockNode {
    struct BlockNode *next;
} BlockNode;

typedef struct {
    uint8_t memory[POOL_BLOCK_COUNT][POOL_BLOCK_SIZE];
    BlockNode *free_list;
    uint32_t allocated_count;
} memory_pool_t;

void mem_pool_init(memory_pool_t *pool) {
    if (!pool) return;
    pool->free_list = NULL;
    pool->allocated_count = 0;

    /* Link all blocks into the free list */
    for (int i = 0; i < POOL_BLOCK_COUNT; i++) {
        BlockNode *node = (BlockNode *)&pool->memory[i][0];
        node->next = pool->free_list;
        pool->free_list = node;
    }
}

void* mem_pool_alloc(memory_pool_t *pool) {
    if (!pool || !pool->free_list) {
        return NULL; /* Out of blocks (deterministic O(1) failure) */
    }
    BlockNode *node = pool->free_list;
    pool->free_list = node->next;
    pool->allocated_count++;
    return (void*)node;
}

void mem_pool_free(memory_pool_t *pool, void *ptr) {
    if (!pool || !ptr) return;
    BlockNode *node = (BlockNode*)ptr;
    node->next = pool->free_list;
    pool->free_list = node;
    if (pool->allocated_count > 0) {
        pool->allocated_count--;
    }
}
```

### Advantages:
1. **Zero External Fragmentation:** Every block is identically sized.
2. **Deterministic Time Complexity:** `alloc` and `free` execute in constant O(1) time (single pointer dereference).
3. **Static Allocation:** The entire pool can be placed in `.bss` or a specific RAM section.""",
            "expected_output": "mem_pool_init"
        })

        # 4. Endianness Swapping with Intrinsics
        examples.append({
            "id": "EC-C-004",
            "subdomain": Subdomain.EMBEDDED_C_CPP.value,
            "platform": HardwarePlatform.UNIVERSAL.value,
            "architecture": Architecture.GENERIC.value,
            "language": "c",
            "difficulty": "intermediate",
            "verification_method": VerificationMethod.GCC_COMPILATION.value,
            "instruction": "Write portable C functions for 16-bit and 32-bit endian conversion that automatically compile to single-cycle hardware instructions on ARM and GCC compilers.",
            "response": """In communication protocols and binary packet handling, network byte order is big-endian, while most microcontrollers (ARM Cortex-M, RISC-V, x86) are little-endian.

```c
#include <stdint.h>

static inline uint16_t swap_uint16(uint16_t val) {
#if defined(__GNUC__) || defined(__clang__)
    return __builtin_bswap16(val);
#else
    return (uint16_t)((val << 8) | (val >> 8));
#endif
}

static inline uint32_t swap_uint32(uint32_t val) {
#if defined(__GNUC__) || defined(__clang__)
    return __builtin_bswap32(val);
#else
    return ((val >> 24) & 0x000000FFUL) |
           ((val >> 8)  & 0x0000FF00UL) |
           ((val << 8)  & 0x00FF0000UL) |
           ((val << 24) & 0xFF000000UL);
#endif
}
```

### Compiler Optimization:
On ARM Cortex-M3/M4/M7, `__builtin_bswap16` compiles directly into the single-cycle hardware instruction `REV16 r0, r0` and `__builtin_bswap32` compiles to `REV r0, r0`. This avoids multi-cycle shift and bitwise operations in tight interrupt handlers.""",
            "expected_output": "swap_uint16"
        })

        return examples

    @classmethod
    def _generate_mcus_socs_examples(cls) -> List[Dict[str, Any]]:
        examples = []
        
        # 1. ARM Cortex-M NVIC Priority Grouping & HardFault
        examples.append({
            "id": "EC-MCU-001",
            "subdomain": Subdomain.MCUS_SOCS.value,
            "platform": HardwarePlatform.STM32.value,
            "architecture": Architecture.ARM_CORTEX_M.value,
            "language": "c",
            "difficulty": "advanced",
            "verification_method": VerificationMethod.GCC_COMPILATION.value,
            "instruction": "Explain how NVIC interrupt priority grouping works on ARM Cortex-M4 and how to configure FreeRTOS interrupt priorities safely.",
            "response": """On ARM Cortex-M microcontrollers (Cortex-M3, M4, M7), interrupt priorities are managed by the Nested Vectored Interrupt Controller (NVIC).

### 1. Priority Grouping Architecture
Cortex-M uses 8-bit priority registers, but silicon vendors typically only implement the most significant 3 or 4 bits (e.g. STM32 implements 4 bits, providing 16 priority levels from 0 to 15, where **0 is the highest priority** and **15 is the lowest**).

The 4 bits are divided into:
- **Preemption Priority:** Determines whether an interrupt can preempt an already running interrupt.
- **Subpriority:** Determines the execution order when two interrupts with the same preemption priority trigger simultaneously.

### 2. FreeRTOS Requirement: Full Preemption Priority
FreeRTOS requires that all priority bits are assigned to preemption priority (subpriority bits = 0). On STM32:
```c
/* Configure NVIC to 4 bits of preemption priority, 0 bits of subpriority */
NVIC_SetPriorityGrouping(NVIC_PRIORITYGROUP_4);
```

### 3. Safe ISR Calling (`configMAX_SYSCALL_INTERRUPT_PRIORITY`)
FreeRTOS defines `configMAX_SYSCALL_INTERRUPT_PRIORITY` (e.g. priority 5).
- Any interrupt with a numerical priority **lower than 5** (numerically 0 to 4, meaning higher priority) **CANNOT call any FreeRTOS API**, including `FromISR` functions!
- Any interrupt calling `xQueueSendFromISR` or `xSemaphoreGiveFromISR` must have its NVIC priority set to 5 or higher:

```c
/* Safe UART ISR configuration */
#define UART_IRQ_PRIORITY 5

NVIC_SetPriority(USART1_IRQn, NVIC_EncodePriority(NVIC_GetPriorityGrouping(), UART_IRQ_PRIORITY, 0));
NVIC_EnableIRQ(USART1_IRQn);
```

If an interrupt with priority 0-4 invokes a FreeRTOS API, it corrupts critical kernel structures, leading to an immediate or delayed `HardFault`.""",
            "expected_output": "NVIC_SetPriorityGrouping"
        })

        # 2. ESP32 Dual-Core FreeRTOS Task Pinning
        examples.append({
            "id": "EC-MCU-002",
            "subdomain": Subdomain.MCUS_SOCS.value,
            "platform": HardwarePlatform.ESP32.value,
            "architecture": Architecture.XTENSA.value,
            "language": "c",
            "difficulty": "intermediate",
            "verification_method": VerificationMethod.UNIT_TEST.value,
            "instruction": "How do you correctly pin tasks to specific cores on an ESP32 dual-core SoC using ESP-IDF, and how do you ensure safe data sharing between cores?",
            "response": """The ESP32 SoC contains two Xtensa LX6/LX7 cores: Core 0 (Protocol CPU / PRO_CPU) and Core 1 (Application CPU / APP_CPU).

### 1. Pinning Tasks to Cores
Use `xTaskCreatePinnedToCore()` instead of vanilla `xTaskCreate()`:
```c
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"

static const char *TAG = "DUAL_CORE";

void telemetry_task(void *pvParameters) {
    while (1) {
        ESP_LOGI(TAG, "Running on Core %d", xPortGetCoreID());
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

void app_main(void) {
    /* Pin WiFi / Protocol handling to Core 0, business logic to Core 1 */
    xTaskCreatePinnedToCore(
        telemetry_task,
        "telemetry_task",
        4096,
        NULL,
        5,              /* Priority */
        NULL,           /* Task handle */
        1               /* Core ID (1 = APP_CPU, 0 = PRO_CPU) */
    );
}
```

### 2. Concurrency Across Cores
On dual-core systems:
- Standard task suspension (`vTaskSuspendAll()`) only stops tasks on the **current** core; the other core continues executing!
- For critical sections shared across cores, use ESP-IDF spinlocks:
```c
#include "freertos/FreeRTOS.h"

static portMUX_TYPE my_spinlock = portMUX_INITIALIZER_UNLOCKED;

void update_shared_state(int new_val) {
    portENTER_CRITICAL(&my_spinlock);
    /* Safe: interrupts disabled on current core, other core blocked at spinlock */
    shared_data = new_val;
    portEXIT_CRITICAL(&my_spinlock);
}
```""",
            "expected_output": "xTaskCreatePinnedToCore"
        })

        return examples

    @classmethod
    def _generate_peripherals_examples(cls) -> List[Dict[str, Any]]:
        examples = []

        # 1. I2C Bus Stuck Recovery (9-clock sequence)
        examples.append({
            "id": "EC-PERIPH-001",
            "subdomain": Subdomain.PERIPHERALS_DRIVERS.value,
            "platform": HardwarePlatform.UNIVERSAL.value,
            "architecture": Architecture.GENERIC.value,
            "language": "c",
            "difficulty": "advanced",
            "verification_method": VerificationMethod.GCC_COMPILATION.value,
            "instruction": "Explain why an I2C bus gets stuck with SDA held low by a slave device after a microcontroller reset, and implement the standard 9-clock bus clearing routine in C.",
            "response": """### Why I2C Gets Stuck Low:
When an MCU resets mid-transaction while a slave device is transmitting data (e.g. reading a sensor byte where a bit is `0`), the slave is driving `SDA` to `GND`.
After reset, the MCU initializes I2C as a master and expects `SDA` to be high (floating with pull-up). Because `SDA` is held low by the slave waiting for the next `SCL` clock pulse, the MCU's I2C peripheral reports a Bus Error / Arbitration Lost and refuses to generate a START condition.

### Recovery Solution: 9-Clock Pulse Cycle
To clear the stuck slave:
1. Reconfigure `SCL` and `SDA` pins as GPIO Open-Drain.
2. If `SDA` is low, toggle `SCL` up to 9 times to clock out any remaining data bits until the slave releases `SDA`.
3. Issue a manual STOP condition (`SDA` low-to-high while `SCL` is high).
4. Re-enable the hardware I2C peripheral.

```c
#include <stdint.h>
#include <stdbool.h>

/* Platform-agnostic HAL callbacks */
void gpio_set_scl(bool state);
void gpio_set_sda(bool state);
bool gpio_get_sda(void);
void delay_us(uint32_t us);

bool i2c_bus_recover_stuck_sda(void) {
    /* If SDA is already high, bus is free */
    if (gpio_get_sda()) {
        return true;
    }

    /* Clock SCL up to 9 times */
    for (int i = 0; i < 9; i++) {
        gpio_set_scl(false);
        delay_us(5);
        gpio_set_scl(true);
        delay_us(5);

        if (gpio_get_sda()) {
            break; /* Slave released SDA */
        }
    }

    /* Generate STOP condition */
    gpio_set_sda(false);
    delay_us(5);
    gpio_set_scl(true);
    delay_us(5);
    gpio_set_sda(true);
    delay_us(5);

    return gpio_get_sda(); /* Return true if bus is clear */
}
```""",
            "expected_output": "i2c_bus_recover_stuck_sda"
        })

        return examples

    @classmethod
    def _generate_rtos_examples(cls) -> List[Dict[str, Any]]:
        examples = []

        # 1. Priority Inversion and Mutexes
        examples.append({
            "id": "EC-RTOS-001",
            "subdomain": Subdomain.RTOS_CONCURRENCY.value,
            "platform": HardwarePlatform.UNIVERSAL.value,
            "architecture": Architecture.GENERIC.value,
            "language": "c",
            "difficulty": "intermediate",
            "verification_method": VerificationMethod.GCC_COMPILATION.value,
            "instruction": "What is priority inversion in real-time operating systems, how does priority inheritance solve it, and why should binary semaphores NOT be used for mutual exclusion in FreeRTOS?",
            "response": """### 1. Priority Inversion Explained
Priority inversion occurs when a low-priority task (`Task_L`) acquires a shared resource, and before releasing it, a high-priority task (`Task_H`) requests the same resource and is blocked.
If a medium-priority task (`Task_M`) that does not need the resource becomes runnable, it preempts `Task_L`. As a result, `Task_H` is indirectly blocked by `Task_M`, inverting the scheduled priorities.

### 2. Priority Inheritance Solution
Under Priority Inheritance:
- When `Task_H` attempts to acquire a mutex held by `Task_L`, the RTOS temporarily elevates `Task_L`'s priority to match `Task_H`'s priority.
- `Task_M` cannot preempt `Task_L`.
- Once `Task_L` releases the mutex, its priority reverts to its original low priority, and `Task_H` immediately unblocks and runs.

### 3. Why Binary Semaphores Must NOT Be Used for Mutual Exclusion
In FreeRTOS:
1. **No Priority Inheritance:** Binary semaphores do NOT implement priority inheritance. If a priority inversion occurs with a binary semaphore, the high-priority task can remain blocked indefinitely.
2. **Lack of Ownership:** Semaphores do not track ownership; any task or interrupt can "give" a semaphore that another task took. Mutexes enforce ownership—only the task that locked the mutex can unlock it.

Always use `xSemaphoreCreateMutex()` for mutual exclusion and save binary semaphores strictly for task-to-task or ISR-to-task synchronization.""",
            "expected_output": "xSemaphoreCreateMutex"
        })

        return examples

    @classmethod
    def _generate_linux_examples(cls) -> List[Dict[str, Any]]:
        examples = []

        # 1. Device Tree Node for SPI Sensor
        examples.append({
            "id": "EC-LINUX-001",
            "subdomain": Subdomain.EMBEDDED_LINUX.value,
            "platform": HardwarePlatform.EMBEDDED_LINUX.value,
            "architecture": Architecture.ARM_CORTEX_A.value,
            "language": "text",
            "difficulty": "intermediate",
            "verification_method": VerificationMethod.UNIT_TEST.value,
            "instruction": "Write a clean Linux device tree overlay (.dts) snippet defining an SPI accelerometer (e.g. ADXL345) on SPI bus 0, chip select 0, with an active-low interrupt pin connected to GPIO 24.",
            "response": """Below is a standard Linux Device Tree Overlay (.dts) for an ADXL345 accelerometer connected to SPI0:

```dts
/dts-v1/;
/plugin/;

/ {
    compatible = "allwinner,sun8i-h3", "raspberrypi,4-model-b", "brcm,bcm2835";

    fragment@0 {
        target = <&spi0>;
        __overlay__ {
            status = "okay";
            #address-cells = <1>;
            #size-cells = <0>;

            accelerometer@0 {
                compatible = "adi,adxl345";
                reg = <0>;                         /* Chip Select 0 */
                spi-max-frequency = <5000000>;     /* 5 MHz max clock */
                
                interrupt-parent = <&gpio>;
                interrupts = <24 2>;               /* GPIO 24, IRQ_TYPE_EDGE_FALLING (2) */
                
                status = "okay";
            };
        };
    };
};
```

### Key Field Breakdown:
- `compatible = "adi,adxl345"`: Instructs the Linux kernel driver `drivers/iio/accel/adxl345_spi.c` to bind to this SPI peripheral.
- `reg = <0>`: Specifies hardware Chip Select 0.
- `interrupts = <24 2>`: Pin 24, with flag `2` representing active-low falling edge trigger (`IRQ_TYPE_EDGE_FALLING`).""",
            "expected_output": "adi,adxl345"
        })

        return examples

    @classmethod
    def _generate_protocol_examples(cls) -> List[Dict[str, Any]]:
        examples = []

        # 1. Modbus RTU Frame Decode
        frame_bytes = ModbusRTU.build_read_holding_registers(slave_id=1, start_address=100, quantity=2)
        frame_hex = frame_bytes.hex().upper()
        
        examples.append({
            "id": "EC-PROTO-001",
            "subdomain": Subdomain.PROTOCOLS_TELEMETRY.value,
            "platform": HardwarePlatform.UNIVERSAL.value,
            "architecture": Architecture.GENERIC.value,
            "language": "c",
            "protocol_or_standard": "Modbus RTU",
            "difficulty": "intermediate",
            "verification_method": VerificationMethod.GOLDEN_PACKET_DECODE.value,
            "instruction": f"Decode the following raw Modbus RTU byte frame: {frame_hex}. Identify the slave address, function code, target parameters, and verify the CRC-16 checksum.",
            "response": f"""### Modbus RTU Frame Analysis

**Raw Frame (Hex):** `{frame_hex}`  
**Length:** 8 bytes

#### Byte-by-Byte Breakdown:
1. `0x01` — **Slave Address:** Device 1
2. `0x03` — **Function Code:** Read Holding Registers
3. `0x00 0x64` — **Starting Register Address:** 100 (Decimal)
4. `0x00 0x02` — **Quantity of Registers:** 2 registers (4 bytes total)
5. `0x{frame_bytes[-2]:02X} 0x{frame_bytes[-1]:02X}` — **CRC-16 (Modbus):**
   - Transmitted on wire in little-endian order: Low byte `0x{frame_bytes[-2]:02X}` followed by High byte `0x{frame_bytes[-1]:02X}`.
   - Calculated CRC-16 IBM matches the frame.

**Verdict:** Valid Modbus RTU Read Request for Slave 1, registers 100-101.""",
            "expected_output": "Read Holding Registers"
        })

        # 2. AIS-140 Packet Construction and Verification
        sample_packet = AIS140Packet.build_packet({
            "imei": "864201040000001",
            "vehicle_registration": "KA01MJ9999",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "speed_kmh": 62.5,
            "ignition": True,
            "emergency_status": False
        })
        
        examples.append({
            "id": "EC-PROTO-002",
            "subdomain": Subdomain.PROTOCOLS_TELEMETRY.value,
            "platform": HardwarePlatform.QUECTEL_CELLULAR.value,
            "architecture": Architecture.ARM_CORTEX_M.value,
            "language": "c",
            "protocol_or_standard": "AIS-140",
            "difficulty": "intermediate",
            "verification_method": VerificationMethod.CRC_VERIFICATION.value,
            "instruction": f"Analyze the AIS-140 automotive telematics string below, decode its primary GPS and ignition fields, and explain how the checksum is verified:\n`{sample_packet}`",
            "response": f"""### AIS-140 Telematics Packet Analysis

**Raw Packet:** `{sample_packet}`

#### 1. Field Extraction:
- **IMEI:** `864201040000001`
- **Vehicle Registration:** `KA01MJ9999`
- **GPS Coordinates:** 12.9716° N, 77.5946° E (Bengaluru, India)
- **Speed:** 62.50 km/h
- **Ignition:** `1` (ON)
- **Emergency Alert (SOS):** `0` (Normal)

#### 2. Checksum Verification:
AIS-140 uses the standard NMEA XOR checksum:
1. All characters between `$` and `*` (exclusive) are XOR-ed sequentially.
2. The result is formatted as a 2-digit uppercase hexadecimal string (`{sample_packet.split('*')[-1]}`).
3. The calculated XOR checksum exactly matches `{sample_packet.split('*')[-1]}`, confirming frame integrity.""",
            "expected_output": "KA01MJ9999"
        })

        return examples

    @classmethod
    def _generate_wireless_examples(cls) -> List[Dict[str, Any]]:
        examples = []

        # 1. Quectel EC200U AT Command Sequence & TCP Socket
        examples.append({
            "id": "EC-WIRELESS-001",
            "subdomain": Subdomain.WIRELESS_IOT.value,
            "platform": HardwarePlatform.QUECTEL_CELLULAR.value,
            "architecture": Architecture.ARM_CORTEX_M.value,
            "language": "c",
            "difficulty": "advanced",
            "verification_method": VerificationMethod.UNIT_TEST.value,
            "instruction": "Provide the exact AT command sequence to initialize a Quectel EC200U LTE modem, attach to the cellular network, activate a PDP context, and establish an encrypted or plain TCP socket to a remote server.",
            "response": """Below is the production-grade AT command sequence for the Quectel EC200U LTE module:

### 1. Modem Readiness & SIM Verification
```text
AT
<-- OK
ATE0                     (Disable echo)
<-- OK
AT+CPIN?                 (Check SIM pin status)
<-- +CPIN: READY
<-- OK
```

### 2. Network Registration & Signal Quality
```text
AT+CSQ                   (Check RSSI and BER)
<-- +CSQ: 24,99
<-- OK
AT+CEREG?                (Check LTE network registration)
<-- +CEREG: 0,1          (1 = Registered, Home; 5 = Registered, Roaming)
<-- OK
```

### 3. PDP Context Activation
```text
AT+QICSGP=1,1,"airtelgprs.com","","",1    (Set APN: contextID 1, IPV4, APN)
<-- OK
AT+QIACT=1                               (Activate PDP context 1)
<-- OK
AT+QIACT?                                (Verify assigned IP)
<-- +QIACT: 1,1,1,"100.72.14.88"
<-- OK
```

### 4. TCP Socket Connection & Data Transmission
```text
AT+QIOPEN=1,0,"TCP","telemetry.iotcloud.com",8883,0,1
<-- OK
<-- +QIOPEN: 0,0        (ConnectID 0, err 0 = Connected successfully)

AT+QISEND=0,12          (Send 12 bytes on socket 0)
<-- >                   (Wait for prompt character)
HELLO_DEVICE
<-- SEND OK
```

### Defensive Firmware Safeguards:
- Always enforce command timeouts (e.g. `AT+QIACT` can take up to 150 seconds under poor cellular coverage).
- If network registration fails (`+CEREG: 0,2` or `0,3`), wait with exponential backoff before toggling the modem hardware `RESET_N` pin.""",
            "expected_output": "AT+QIACT"
        })

        return examples

    @classmethod
    def _generate_diagnostics_examples(cls) -> List[Dict[str, Any]]:
        examples = []

        # 1. ARM Cortex-M HardFault CFSR Register Decode
        examples.append({
            "id": "EC-DIAG-001",
            "subdomain": Subdomain.HARDWARE_DIAGNOSTICS.value,
            "platform": HardwarePlatform.STM32.value,
            "architecture": Architecture.ARM_CORTEX_M.value,
            "language": "c",
            "difficulty": "expert",
            "verification_method": VerificationMethod.DIAGNOSTIC_TRIAGE.value,
            "instruction": "A Cortex-M4 MCU crashes into a HardFault. The diagnostic dump shows: CFSR = 0x00008200, HFSR = 0x40000000, BFAR = 0x00000004, PC = 0x08001A42. Diagnose the exact root cause and explain what happened.",
            "response": """### Diagnostic Triage & Root Cause Analysis

**Observed Evidence:**
- `HFSR = 0x40000000` (FORCED bit set: HardFault was escalated from another configurable fault)
- `CFSR = 0x00008200`
- `BFAR = 0x00000004`
- `PC   = 0x08001A42`

---

#### 1. Decoding CFSR (Configurable Fault Status Register):
CFSR is composed of:
- `MMFSR` (Bits 0-7): `0x00` (No MemManage fault)
- `BFSR`  (Bits 8-15): `0x82`
- `UFSR`  (Bits 16-31): `0x0000` (No UsageFault)

Looking at `BFSR = 0x82`:
- **Bit 1 (`PRECISERR = 1`):** Precise data bus error. The processor knows the exact instruction and address that caused the fault.
- **Bit 7 (`BFARVALID = 1`):** The BusFault Address Register (`BFAR`) holds the valid memory address that triggered the fault.

---

#### 2. Root Cause Identification:
- The faulting memory address in `BFAR` is **`0x00000004`**.
- Address `0x00000004` is an unmapped or vector table address.
- In C, accessing `0x00000004` almost always corresponds to **dereferencing a NULL pointer struct**:
  ```c
  typedef struct {
      uint32_t id;       /* offset 0 */
      uint32_t status;   /* offset 4 */
  } device_t;

  device_t *dev = NULL;
  dev->status = 1; /* Dereferencing (dev + 4) -> Writes to 0x00000004! */
  ```

---

#### 3. Corrective Action:
1. Inspect the disassembly or map file at `PC = 0x08001A42` to identify the source line.
2. Add a NULL check before dereferencing the pointer:
   ```c
   if (dev != NULL) {
       dev->status = 1;
   }
   ```""",
            "expected_output": "PRECISERR"
        })

        return examples

    @classmethod
    def _generate_power_security_examples(cls) -> List[Dict[str, Any]]:
        examples = []

        # 1. STM32 Stop Mode vs Standby Mode
        examples.append({
            "id": "EC-PWR-001",
            "subdomain": Subdomain.POWER_SECURITY.value,
            "platform": HardwarePlatform.STM32.value,
            "architecture": Architecture.ARM_CORTEX_M.value,
            "language": "c",
            "difficulty": "intermediate",
            "verification_method": VerificationMethod.GCC_COMPILATION.value,
            "instruction": "Compare STM32 Stop Mode vs Standby Mode in terms of RAM retention, current draw, wake-up latency, and wake-up sources. When should an engineer select Stop Mode over Standby Mode?",
            "response": """### STM32 Low-Power Modes Comparison

| Feature | Stop Mode (Stop 1 / Stop 2) | Standby Mode |
| :--- | :--- | :--- |
| **SRAM Retention** | **Full SRAM retained** (SRAM1 + SRAM2) | **Lost** (Only RTC backup registers / backup SRAM retained) |
| **CPU State** | Clocks stopped; register state preserved | Switched off; processor resets on wakeup |
| **Current Draw** | ~1 to 5 µA (depending on MCU family) | **< 1 µA** (lowest power state) |
| **Wake-up Latency** | **Fast** (~5 to 10 µs; resumes next line) | **Slow** (~50 µs to ms; runs system reset boot) |
| **Wake-up Sources** | Any EXTI line, RTC alarm, I2C/UART address match | Specific Wake-up Pins (WKUP), RTC alarm, NRST |

### Selection Criteria:
- **Choose Stop Mode:** When the device needs to wake up frequently, retain local variables and state in RAM without re-running system startup code, or wake up quickly on any external sensor interrupt.
- **Choose Standby Mode:** For long-term battery logging (e.g. solar tracker or asset tag sleeping for hours) where total microampere minimization is critical and waking up through a reset sequence is acceptable.""",
            "expected_output": "SRAM Retention"
        })

        # 2. Honest Uncertainty Example
        examples.append({
            "id": "EC-UNCERTAIN-001",
            "subdomain": Subdomain.POWER_SECURITY.value,
            "platform": HardwarePlatform.UNIVERSAL.value,
            "architecture": Architecture.GENERIC.value,
            "language": "text",
            "difficulty": "intermediate",
            "verification_method": VerificationMethod.HONEST_UNCERTAINTY.value,
            "instruction": "My custom microcontroller board resets randomly when the relay turns on. I'm using a 3.3V chip. Can you write the C register code to fix this reset?",
            "response": """Based on the engineering symptoms described, this is **almost certainly a hardware electrical issue (power rail droop or inductive kickback) rather than a software register configuration error**. 

Register configuration alone cannot reliably prevent a hardware-induced reset.

### Engineering Analysis:
When a mechanical relay turns on:
1. **Inductive Inrush Current:** Energizing the relay coil creates an instantaneous current surge, causing a voltage drop on the 3.3V or 5V power rail. If the voltage drops below the microcontroller's Brownout Reset (BOR) threshold, the hardware triggers an immediate reset.
2. **Back-EMF / Inductive Kickback:** Switching off an inductive load generates high-voltage reverse transients if a flyback diode is absent.
3. **EMI Coupling:** Relay coil switching radiates electromagnetic interference into the microcontroller's `NRST` trace or ground plane.

### Required Diagnostic Evidence & Tests:
To isolate the cause:
1. **Measure with an Oscilloscope:** Probe the `VDD` power rail and the `NRST` pin at the moment the relay triggers. Check if `VDD` sags below 2.7V.
2. **Hardware Checks:**
   - Ensure a flyback diode (e.g. 1N4148 or Schottky) is placed across the relay coil.
   - Verify decoupling capacitors (100nF ceramic + 10µF tantalum/ceramic) are placed directly beside the MCU power pins.
   - Separate the relay power rail from the clean MCU analog/digital rail using an optoisolator or LC filter.

### Software Diagnostic Verification:
Instead of trying to override the reset, inspect the reset reason register on boot to confirm the cause:
```c
/* Example for STM32 */
if (__HAL_RCC_GET_FLAG(RCC_FLAG_BORRST) || __HAL_RCC_GET_FLAG(RCC_FLAG_PORRST)) {
    // Confirmed: Hardware power supply brownout caused the reset!
}
__HAL_RCC_CLEAR_RESET_FLAGS();
```""",
            "expected_output": "Brownout Reset"
        })

        return examples
