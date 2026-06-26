from io import BytesIO
from datetime import date, timedelta
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import logging

import numpy as np
from scipy.interpolate import make_interp_spline
from asyncpg import Record
from twilight_vk.http.async_http import Http

logger = logging.getLogger("rank-render")

class RankCard:

    def __init__(self,
                 user: Record,
                 member: Record,
                 data: list[Record],
                 font_path: str = None) -> None:
        self._user = user
        self._member = member
        self._data = data or []
        self._font_path = font_path or "assets/stats/fonts/MyriadPro-Regular.otf"
        self._image: Image.Image

        self.http = Http()

        self._avatar = None
        self._background = Image.open("assets/stats/img/background.png").resize(800, 571).convert("RGBA")

        self._width, self._height = 800, 300
    
    async def _draw_avatar(self, 
                           size: int = 100):
        
        try:
            _resp = await self.http.get(self._user.get("photo_100", ""))
            await self.http.close()
            avatar = Image.open(
                BytesIO(_resp.content)
            ).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
        except Exception:
            logger.error("Error with getting avatar. Avatar will be replaced on blank", exc_info = True)
            avatar = Image.new("RGBA", (size, size), (50,50,50,255))
            draw = ImageDraw.Draw(avatar)
            draw.ellipse((0, 0, size, size), fill=(50,50,50,255))

        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill = 255)
        avatar.putalpha(mask)

        self._avatar = self._avatar_outline(avatar, size)

    def _avatar_outline(self, 
                        avatar: Image.Image,
                        size: int = 100, 
                        border_size: int = 4,
                        offset: int = 2):

        total_size = size + 2 * (offset + border_size)
        center = total_size // 2

        gradient = Image.new("RGBA", (total_size, total_size), (0, 0, 0, 0))
        draw_gradient = ImageDraw.Draw(gradient)
        for x in range(total_size):
            t = x / (total_size - 1)
            r = int(0 + (255 - 0) * t)
            g = int(108 + (0 - 108) * t)
            b = int(255 + (108 - 255) * t)
            draw_gradient.rectangle((x, 0, x + 1, total_size), fill = (r, g, b, 255))

        mask = Image.new("L", (total_size, total_size), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, total_size - 1, total_size - 1), fill = 255)
        inner_radius = size // 2 + offset
        draw_mask.ellipse((center - inner_radius, center - inner_radius,
                           center + inner_radius, center + inner_radius), fill = 0)
        
        gradient.putalpha(mask)

        avatar_resized = avatar.resize((size, size), Image.Resampling.LANCZOS)
        result = Image.new("RGBA", (total_size, total_size), (0, 0, 0, 0))
        avatar_pos = offset + border_size
        result.paste(avatar_resized, (avatar_pos, avatar_pos))

        result = Image.alpha_composite(result, gradient)
        return result
    
    def _draw_progress_bar(self, 
                           draw: ImageDraw.ImageDraw, 
                           x: int, y: int, 
                           width: int, height: int, 
                           progress: int, 
                           color_start: tuple[int, int, int], color_end: tuple[int, int, int]):
        
        bar = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(bar)

        radius = height // 2

        draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=(50, 50, 50, 180))

        if progress > 0:

            fill_width = int(width * progress)

            grad = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            grad_draw = ImageDraw.Draw(grad)
            
            for i in range(fill_width):
                t = i / width
                r = int(color_start[0] + (color_end[0] - color_start[0]) * t)
                g = int(color_start[1] + (color_end[1] - color_start[1]) * t)
                b = int(color_start[2] + (color_end[2] - color_start[2]) * t)
                grad_draw.rectangle((x + i, y, x + i + 1, y + height), fill = (r, g, b, 220))

            mask_progress = Image.new("L", (width, height), 0)
            mask_draw = ImageDraw.Draw(mask_progress)
            mask_draw.rectangle((0, 0, fill_width, height), fill=255)

            grad = Image.composite(grad, Image.new("RGBA", (width, height), (0, 0, 0, 0)), mask_progress)

            mask_rounded = Image.new("L", (fill_width, height), 0)
            mask_rounded_draw = ImageDraw.Draw(mask_rounded)
            mask_rounded_draw.rounded_rectangle((0, 0, fill_width, height),
                                            radius=radius,
                                            corners=(0, radius, radius, 0))
            
            grad_final = Image.new("RGBA", (fill_width, height), (0, 0, 0, 0))
            grad_final.paste(grad.crop((0, 0, fill_width, height)), (0, 0), mask_rounded)

            bar.paste(grad_final, (0, 0), grad_final)

        return bar

    def _make_graph(self, data, days_labels):

        fig, ax = plt.subplots(figsize=(7, 1.25), dpi=100)
        fig.patch.set_alpha(0)
        ax.patch.set_alpha(0)

        days = np.arange(len(data))
        if len(data) > 3:
            x_smooth = np.linspace(days.min(), days.max(), 300)
            spline = make_interp_spline(days, data, k=3)
            y_smooth = spline(x_smooth)
            ax.plot(x_smooth, y_smooth, color='#0661fb', linewidth=2, alpha=0.8)
        else:
            ax.plot(days, data, color='#0661fb', linewidth=2, alpha=0.8)

        ax.plot(days, data, 'o', color='#0661fb', markerfacecolor='none',
                markeredgewidth=2, markersize=4)

        ax.set_xticks(days)
        ax.set_xticklabels(days_labels, color='#0661fb', fontsize=8)
        ax.tick_params(axis='y', colors='#0661fb', labelsize=8)
        ax.set_ylim(0, max(data)*1.2 if max(data)>0 else 1)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(False)
        ax.spines['left'].set_color('#0661fb')
        ax.grid(True, linestyle='--', alpha=0.1, color='#0661fb')

        buf = BytesIO()
        plt.savefig(buf, format='png', transparent=True, bbox_inches='tight', pad_inches=0.1)
        buf.seek(0)
        plt.close()
        return Image.open(buf).convert("RGBA")
    
    def _validateData(self):
        '''
        Подготовка данных для отрисовки
        '''
        _today = date.today()

        _activity = {_today - timedelta(days = i): 0 for i in range(13, -1, -1)}

        for _record in self._data:

            _day = _record["date"]
            if _day in _activity:
                _activity[_day] = _record["activity"]
        
        sorted_days = sorted(_activity.keys())
        self._weekly_activity = [_activity[day] for day in sorted_days]
        self._days = [day.strftime("%d.%m") for day in sorted_days]

    async def render(self) -> Image.Image:

        try:
            self._validateData()
            
            '''Background rendering'''
            bg = Image.new("RGBA", (self._width, self._height), (30,30,30,255))
            draw = ImageDraw.Draw(bg)
            bg.paste(self._background, (0, -125), self._background)

            '''Avatar rendering'''
            _avatar_size = 100
            _avatar_x, _avatar_y = 45, 15

            await self._draw_avatar(_avatar_size)
            bg.paste(self._avatar, (_avatar_x, _avatar_y), self._avatar)

            _name_x, _name_y = 175, 20
            font_name = ImageFont.truetype(self._font_path, 30)
            _nickname = f"{self._user["nickname"]}"
            _full_name = f"{self._user["first_name"]} {self._user["last_name"]}"
            draw.text((_name_x, _name_y), _nickname or _full_name, font = font_name, fill = '#8fc5ff')

            _screen_name_x, _screen_name_y = _name_x, _name_y + 30
            font_screen_name = ImageFont.truetype(self._font_path, 16)
            draw.text((_screen_name_x, _screen_name_y), f"@{self._member['screen_name']}", font=font_screen_name, fill='#39a1ff')

            _level_x, _level_y = _name_x, _name_y + 60
            font_level = ImageFont.truetype(self._font_path, 18)
            level_text = f"Уровень {self._member['level']}  •  ({self._member['xp_per_level']} exp. / {self._member['max_xp_per_level']} exp.)"
            draw.text((_level_x, _level_y), level_text, font=font_level, fill='#39a1ff')

            _bar_x, _bar_y = 170, 105
            _bar_width, _bar_height = 600, 5
            progress = self._member['xp_per_level'] / self._member.get('max_xp_per_level', 1)
            progress = min(max(progress, 0), 1)
            bar_img = self._draw_progress_bar(_bar_width, _bar_height, progress, 
                                    (0, 108, 255), (255, 0, 108))
            bg.paste(bar_img, (_bar_x, _bar_y), bar_img)

            _graph_x, _graph_y = 30, 140
            
            if hasattr(self, '_weekly_activity') and hasattr(self, '_days'):

                graph_img = self._make_graph(self._weekly_activity, self._days)
                
                graph_width, graph_height = 700, 125
                graph_img = graph_img.resize((graph_width, graph_height), Image.Resampling.LANCZOS)
                
                bg.paste(graph_img, (_graph_x, _graph_y), graph_img)

            self._image = bg
        
        except Exception as exc:
            logger.error(f"Renderer error: {exc}", exc_info = True)
    
    def save(self, 
             path: str):
        self._image.save(path, format='PNG')