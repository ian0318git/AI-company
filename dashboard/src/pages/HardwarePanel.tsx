import { Cpu, Usb, Monitor } from 'lucide-react'

export default function HardwarePanel() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Hardware Panel</h2>

      <div className="grid grid-cols-2 gap-4 mb-8">
        {[
          { title: 'Connected Devices', icon: Usb, value: 'Use hw_detect_board', color: 'text-blue-400' },
          { title: 'Default Board', icon: Cpu, value: 'M5Stack Core S3', color: 'text-green-400' },
          { title: 'Default Port', icon: Monitor, value: '/dev/ttyACM0', color: 'text-yellow-400' },
        ].map(({ title, icon: Icon, value, color }) => (
          <div key={title} className="border border-[hsl(var(--border))] rounded-lg p-4 bg-white/5">
            <div className="flex items-center gap-2 mb-2">
              <Icon className={`w-4 h-4 ${color}`} />
              <span className="text-sm text-gray-400">{title}</span>
            </div>
            <p className="font-mono text-sm">{value}</p>
          </div>
        ))}
      </div>

      <div className="border border-[hsl(var(--border))] rounded-lg p-6 bg-white/5 mb-6">
        <h3 className="text-lg font-semibold mb-4">M5Stack Core S3 — Quick Reference</h3>
        <div className="grid grid-cols-2 gap-2 text-sm">
          {[
            ['MCU', 'ESP32-S3 (dual-core 240MHz)'],
            ['SRAM', '512KB internal + 8MB PSRAM'],
            ['Flash', '16MB Quad SPI'],
            ['Display', 'ILI9342C 320x240 TFT (SPI)'],
            ['Touch', 'FT6336U I2C (addr: 0x38)'],
            ['IMU', 'BMI270 + BMM150 I2C'],
            ['Microphone', 'SPM1423 PDM MEMS'],
            ['I2C Bus', 'SDA=8, SCL=9 (shared)'],
            ['Grove I2C', 'SDA=1, SCL=2'],
            ['SD Card', 'SPI (CS=5, shared MOSI/SCLK)'],
            ['RGB LED', 'GPIO 21 (SK6812)'],
            ['Boot Button', 'GPIO 0'],
          ].map(([label, value]) => (
            <div key={label} className="flex justify-between py-1 border-b border-[hsl(var(--border))]">
              <span className="text-gray-400">{label}</span>
              <span className="font-mono text-xs">{value}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="border border-[hsl(var(--border))] rounded-lg p-4 bg-white/5">
        <h3 className="font-semibold mb-2 text-sm">MCP Hardware Tools</h3>
        <div className="space-y-1 text-xs text-gray-400">
          <p><code className="text-blue-400">hw_detect_board</code> — Scan USB for connected dev boards</p>
          <p><code className="text-blue-400">hw_pinout_get</code> — Get pinout for a specific board</p>
          <p><code className="text-blue-400">hw_build</code> — Compile firmware (PlatformIO)</p>
          <p><code className="text-blue-400">hw_flash_firmware</code> — Upload firmware to board</p>
          <p><code className="text-blue-400">hw_serial_monitor</code> — Read serial output</p>
        </div>
      </div>
    </div>
  )
}
