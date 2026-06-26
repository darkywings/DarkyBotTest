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
                 user: dict,
                 data: list[Record],
                 font_path: str = None) -> None:
        self._user = user
        self._data = data or []
        self._font_path = font_path or "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        self._image: Image.Image

        self.http = Http()

        self._avatar = None
        self._background = Image.open("assets/stats_background.png").convert("RGBA")

        self._width, self._height = 800, 600
    
    async def _draw_avatar(self, 
                           size: int = 100):
        
        try:
            _resp = await self.http.get(self._user.get("photo_100", ""))
            await self.http.close()
            avatar = Image.open(
                BytesIO(_resp.content)
            ).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
        except Exception:
            avatar = Image.new("RGBA", (size, size), (128,128,128,255))
            draw = ImageDraw.Draw(avatar)
            draw.ellipse((0,0,size,size), fill=(128,128,128,255))

        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        avatar.putalpha(mask)
        self._avatar = self._avatar_outline(avatar, size)

    def _avatar_outline(self, 
                        avatar: Image.Image,
                        size: int = 100, 
                        border_size: int = 4):

        border_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw_border = ImageDraw.Draw(border_img)

        for i in range(border_size):
            t = i / border_size
            r = int(66 + (233 - 66) * t)
            g = int(133 + (30 - 133) * t)
            b = int(244 + (99 - 244) * t)
            draw_border.ellipse((i, i, size - i, size - i), outline = (r, g, b, 255), width = 1)
        
        return Image.alpha_composite(avatar, border_img)
    
    def _draw_progress_bar(self, 
                           draw: ImageDraw.ImageDraw, 
                           x: int, y: int, 
                           width: int, height: int, 
                           progress: int, 
                           color_start: tuple[int, int, int], color_end: tuple[int, int, int]):
        
        draw.rectangle((x, y, x + width, y + height), fill = (50, 50, 50, 180))

        if progress > 0:

            fill_width = int(width * progress)
            
            for i in range(fill_width):
                t = i / fill_width
                r = int(color_start[0] + (color_end[0] - color_start[0]) * t)
                g = int(color_start[1] + (color_end[1] - color_start[1]) * t)
                b = int(color_start[2] + (color_end[2] - color_start[2]) * t)
                draw.rectangle((x + i, y, x + i + 1, y + height), fill = (r, g, b, 220))

    def _make_graph(self, data, days_labels):

        fig, ax = plt.subplots(figsize=(6, 2.5), dpi=100)
        fig.patch.set_alpha(0)
        ax.patch.set_alpha(0)

        days = np.arange(len(data))
        if len(data) > 3:
            x_smooth = np.linspace(days.min(), days.max(), 300)
            spline = make_interp_spline(days, data, k=3)
            y_smooth = spline(x_smooth)
            ax.plot(x_smooth, y_smooth, color='#4A90D9', linewidth=2, alpha=0.8)
        else:
            ax.plot(days, data, color='#4A90D9', linewidth=2, alpha=0.8)

        ax.plot(days, data, 'o', color='#4A90D9', markerfacecolor='none',
                markeredgewidth=2, markersize=8)

        ax.set_xticks(days)
        ax.set_xticklabels(days_labels, color='white', fontsize=9)
        ax.tick_params(axis='y', colors='white', labelsize=8)
        ax.set_ylim(0, max(data)*1.2 if max(data)>0 else 1)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.grid(True, linestyle='--', alpha=0.3, color='white')

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
        self._days = [day.strftime("%a") for day in sorted_days]

    async def render(self) -> Image.Image:

        try:
            self._validateData()
            
            bg = self._background.resize((self._width, self._height)).convert("RGBA")
            draw = ImageDraw.Draw(bg)

            '''Positions'''
            _avatar_size = 100
            _avatar_x, _avatar_y = 40, 40

            _name_x = _avatar_x + _avatar_size + 3
            _name_y = 50

            _nickname_x, _nickname_y = _name_x, _name_y + 40

            _level_x = _name_x
            _level_y = _nickname_y + 60

            _bar_x = _name_x
            _bar_y = _level_y + 30
            _bar_width = 400
            _bar_height = 20

            _graph_x = _avatar_x
            _graph_y = _avatar_y + _avatar_size + 50

            await self._draw_avatar(_avatar_size)
            bg.paste(self._avatar, (_avatar_x, _avatar_y), self._avatar)
        
            font_name = ImageFont.truetype(self._font_path, 28)
            font_nick = ImageFont.truetype(self._font_path, 18)
            font_level = ImageFont.truetype(self._font_path, 18)

            full_name = f"{self._user['first_name']} {self._user.get('last_name', '')} ({self._user.get("nickname", " - ")})".strip()
            draw.text((_name_x, _name_y), full_name, font = font_name, fill = '#88F')

            if self._user.get('screen_name'):
                draw.text((_nickname_x, _nickname_y), f"@{self._user['screen_name']}", font=font_nick, fill='#55D')

            level_text = f"Уровень {self._user['level']} • ({self._user['xp_per_level']} exp. / {self._user['max_xp_per_level']} exp.)"
            draw.text((_level_x, _level_y), level_text, font=font_level, fill='#55F')

            progress = self._user['xp_per_level'] / self._user.get('max_xp_per_level', 1)
            progress = min(max(progress, 0), 1)
            self._draw_progress_bar(draw, _bar_x, _bar_y, _bar_width, _bar_height,
                                    progress, (66, 133, 244), (233, 30, 99))
            
            draw.text((_bar_x + _bar_width + 10, _bar_y), f"{int(progress*100)}%",
                    font=font_level, fill='#FFF')
            
            if hasattr(self, '_weekly_activity') and hasattr(self, '_days'):

                graph_img = self._make_graph(self._weekly_activity, self._days)
                
                graph_width = self._width - 80
                aspect = graph_img.width / graph_img.height
                graph_height = int(graph_width / aspect)
                graph_img = graph_img.resize((graph_width, graph_height), Image.Resampling.LANCZOS)
                
                bg.paste(graph_img, (40, _graph_y), graph_img)

            self._image = bg
        
        except Exception as exc:
            logger.error(f"Renderer error: {exc}", exc_info = True)
    
    def save(self, 
             path: str):
        self._image.save(path, format='PNG')