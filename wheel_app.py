from nicegui import ui, app
import random
import math
import pandas as pd
from pathlib import Path

class WheelOfFortune:
    def __init__(self):
        self.participants = []
        self.colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', 
            '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2',
            '#F8B739', '#52B788', '#E76F51', '#2A9D8F'
        ]
        self.spinning = False
        self.winner_number = None
        self.current_rotation = 0
        
    def add_participant(self, name):
        if name and name.strip():
            self.participants.append(name.strip())
            self.update_ui()
    
    def load_from_excel(self, e):
        try:
            # خواندن فایل از محتوای آپلود شده
            import io
            content = e.content.read()
            df = pd.read_excel(io.BytesIO(content), header=None)
            
            count = 0
            for name in df.iloc[:, 0]:
                if pd.notna(name) and str(name).strip():
                    self.participants.append(str(name).strip())
                    count += 1
            
            self.update_ui()
            ui.notify(f'✅ {count} شرکت‌کننده از فایل اضافه شد', type='positive')
        except Exception as e:
            ui.notify(f'❌ خطا در بارگذاری فایل: {str(e)}', type='negative')
    
    def clear_all(self):
        self.participants.clear()
        self.winner_number = None
        self.update_ui()
        ui.notify('🗑 همه شرکت‌کننده‌ها حذف شدند', type='info')
    
    def spin_wheel(self):
        if len(self.participants) < 2:
            ui.notify('⚠️ حداقل ۲ شرکت‌کننده لازم است', type='warning')
            return
        
        if self.spinning:
            return
        
        self.spinning = True
        self.winner_number = random.randint(0, len(self.participants) - 1)
        
        # محاسبه زاویه نهایی
        angle_per_section = 360 / random.randint(1, len(self.participants))
        
        # یه offset تصادفی داخل بخش برنده (تا دقیقاً وسط نیفته)
        random_offset = random.uniform(-angle_per_section * 0.3, angle_per_section * 0.3)
        
        # زاویه وسط بخش برنده
        winner_center_angle = self.winner_number * angle_per_section + angle_per_section / 2 + random_offset
        
        # چرخش‌های اضافی
        extra_rotations = random.randint(5, 8) * 360
        
        # نرمال کردن current_rotation به بین 0 تا 360
        normalized_current = self.current_rotation % 360
        
        # محاسبه زاویه نهایی
        # فلش در بالا (زاویه 0 در SVG) قرار داره
        # بخش‌ها از -90 درجه شروع میشن، پس باید چرخ رو برعکس بچرخونیم
        # تا بخش برنده زیر فلش قرار بگیره
        target_angle = (winner_center_angle) % 360
        final_rotation = self.current_rotation + extra_rotations + (target_angle - normalized_current)
        
        # انیمیشن به صورت تدریجی
        start_rotation = self.current_rotation
        steps = 60
        duration = 3000  # 3 ثانیه
        
        def animate_step(step):
            if step < steps:
                progress = step / steps
                # ease-out cubic
                eased = 1 - pow(1 - progress, 3)
                self.current_rotation = start_rotation + (final_rotation - start_rotation) * eased
                self.draw_wheel()
                ui.timer(duration / 1000 / steps, lambda: animate_step(step + 1), once=True)
            else:
                self.current_rotation = final_rotation
                self.draw_wheel()
                self.show_winner()
        
        animate_step(0)
    
    def show_winner(self):
        self.spinning = False
        winner_name = self.participants[self.winner_number]
        winner_num = self.winner_number + 1
        
        # نمایش پیام برنده
        with ui.dialog() as dialog, ui.card().classes('p-6 text-center'):
            ui.label('🎉').classes('text-6xl mb-4')
            ui.label(f'برنده: شماره {winner_num}').classes('text-2xl font-bold mb-2')
            ui.label(f'({winner_name})').classes('text-xl text-blue-600 mb-4')
            ui.button('بستن', on_click=dialog.close).classes('bg-blue-500 text-white')
        
        dialog.open()
        
        # حذف برنده از لیست
        self.participants.pop(self.winner_number)
        self.winner_number = None
        self.update_ui()
    
    def draw_wheel(self):
        if not hasattr(self, 'canvas'):
            return
        
        self.canvas.clear()
        
        if len(self.participants) == 0:
            with self.canvas:
                ui.html('''
                    <svg viewBox="0 0 400 400" style="width: 100%; height: 100%;">
                        <circle cx="200" cy="200" r="150" fill="#e0e0e0" stroke="#999" stroke-width="3"/>
                        <text x="200" y="210" text-anchor="middle" font-size="20" fill="#666">
                            هیچ شرکت‌کننده‌ای وجود ندارد
                        </text>
                    </svg>
                ''')
            return
        
        n = len(self.participants)
        angle_per_section = 360 / n
        
        rotation = self.current_rotation if hasattr(self, 'current_rotation') else 0
        
        svg_parts = [f'<svg viewBox="0 0 400 400" style="width: 100%; height: 100%;">']
        svg_parts.append(f'<g transform="rotate({rotation} 200 200)">')
        
        # رسم بخش‌های گردونه
        for i in range(n):
            color = self.colors[i % len(self.colors)]
            start_angle = i * angle_per_section - 90
            end_angle = (i + 1) * angle_per_section - 90
            
            # محاسبه نقاط برای path
            start_rad = math.radians(start_angle)
            end_rad = math.radians(end_angle)
            
            x1 = 200 + 150 * math.cos(start_rad)
            y1 = 200 + 150 * math.sin(start_rad)
            x2 = 200 + 150 * math.cos(end_rad)
            y2 = 200 + 150 * math.sin(end_rad)
            
            # رسم بخش
            large_arc = 1 if angle_per_section > 180 else 0
            path = f'M 200,200 L {x1},{y1} A 150,150 0 {large_arc},1 {x2},{y2} Z'
            svg_parts.append(f'<path d="{path}" fill="{color}" stroke="white" stroke-width="2"/>')
            
            # نوشتن شماره
            mid_angle = start_angle + angle_per_section / 2
            mid_rad = math.radians(mid_angle)
            text_x = 200 + 100 * math.cos(mid_rad)
            text_y = 200 + 100 * math.sin(mid_rad)
            
            svg_parts.append(f'''
                <text x="{text_x}" y="{text_y}" text-anchor="middle" 
                      dominant-baseline="middle" font-size="24" 
                      font-weight="bold" fill="white" 
                      transform="rotate({-rotation} {text_x} {text_y})">
                    {i + 1}
                </text>
            ''')
        
        # دایره مرکزی
        svg_parts.append('<circle cx="200" cy="200" r="20" fill="white" stroke="#333" stroke-width="2"/>')
        
        svg_parts.append('</g>')
        
        # فلش بالا (ثابت)
        # svg_parts.append('''
        #     <path d="M 200,80 L 215,50 L 185,50 Z" fill="red" stroke="#333" stroke-width="2"/>
        # ''')
        
        svg_parts.append('</svg>')
        
        with self.canvas:
            ui.html(''.join(svg_parts))
    
    def update_ui(self):
        self.draw_wheel()
        self.participants_list.clear()
        with self.participants_list:
            if self.participants:
                for i, name in enumerate(self.participants, 1):
                    ui.label(f'{i}. {name}').classes('text-sm mb-1')
            else:
                ui.label('هیچ شرکت‌کننده‌ای وجود ندارد').classes('text-gray-400 text-sm')

# ایجاد برنامه
wheel = WheelOfFortune()

# استایل CSS
ui.add_head_html('''
<style>
    body {
        background-color: white !important;
    }
    .spinning {
        animation: spin 3s cubic-bezier(0.17, 0.67, 0.12, 0.99);
    }
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(1800deg); }
    }
</style>
''')

# رابط کاربری
with ui.row().classes('w-full h-screen p-4 gap-4'):
    # ستون چپ - کنترل‌ها
    with ui.column().classes('w-1/4 gap-4'):
        ui.label('➕ افزودن شرکت‌کننده').classes('text-lg font-bold mb-2')
        
        # ورودی نام
        name_input = ui.input('نام').classes('w-full').props('outlined dense')
        name_input.on('keydown.enter', lambda: (
            wheel.add_participant(name_input.value),
            name_input.set_value('')
        ))
        
        ui.button('افزودن', 
                 on_click=lambda: (
                     wheel.add_participant(name_input.value),
                     name_input.set_value('')
                 )).classes('w-full bg-green-500 text-white')
        
        # بارگذاری فایل
        ui.label('📁 بارگذاری از Excel').classes('text-lg font-bold mt-4 mb-2')
        
        def handle_upload(e):
            wheel.load_from_excel(e)
            upload.reset()  # پاک کردن فایل انتخاب شده
        
        upload = ui.upload(on_upload=handle_upload,
                          auto_upload=True).classes('w-full').props('accept=".xlsx,.xls"')
        
        ui.space()
        
        # دکمه‌های اصلی
        ui.button('🎯 چرخاندن گردونه', 
                 on_click=wheel.spin_wheel).classes('w-full bg-blue-500 text-white text-lg py-3')
        
        ui.button('🗑 حذف همه', 
                 on_click=wheel.clear_all).classes('w-full bg-red-500 text-white')
    
    # ستون مرکزی - گردونه
    with ui.column().classes('w-2/4 items-center justify-center'):
        wheel.canvas = ui.element('div').classes('w-full max-w-md')
        wheel.draw_wheel()
    
    # ستون راست - لیست شرکت‌کننده‌ها
    with ui.column().classes('e-2/4 gap-2'):
        ui.label('👥 لیست شرکت‌کننده‌ها').classes('text-lg font-bold mb-2')
        with ui.card().classes('e-full p-4 overflow-auto').style('max-height: 80vh'):
            wheel.participants_list = ui.column().classes('gap-1')
            wheel.update_ui()

ui.run(native=True, window_size=(1400, 800), title='گردونه شانس')