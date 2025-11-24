import flet as ft
from datetime import datetime
import os
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(page: ft.Page):
    # 页面配置
    page.title = "Flet相机Demo - 优化版"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window_width = 400
    page.window_height = 700

    # 状态管理类
    class CameraState:
        def __init__(self):
            self.camera = None
            self.preview_img = None
            self.rotation = 0
            self.is_camera_ready = False
            self.last_captured_path = None

        def update_status(self, message):
            status_text.value = message
            page.update()

    state = CameraState()

    # 工具函数
    def get_storage_path():
        """获取合适的存储路径"""
        if page.platform == ft.Platform.ANDROID:
            # Android使用外部存储
            base_path = "/storage/emulated/0/DCIM/FletCamera"
        else:
            # 其他平台使用当前目录
            base_path = "./photos"

        Path(base_path).mkdir(parents=True, exist_ok=True)
        return base_path

    def create_camera_component():
        """创建相机组件"""
        try:
            return ft.Camera(
                width=page.width,
                height=page.height * 0.6,
                fit=ft.ImageFit.COVER,
                visible=True,
            )
        except Exception as e:
            logger.error(f"创建相机组件失败: {e}")
            return None

    # 事件处理函数
    async def check_permissions(e):
        """检查并请求权限"""
        try:
            # 检查当前权限状态
            if (page.client_storage.get("camera_granted") and
                    page.client_storage.get("storage_granted")):
                await init_camera()
                return

            # 请求权限
            permissions = await page.request_permissions_async(
                ["camera", "storage", "media_library"]
            )

            if permissions:
                page.client_storage.set("camera_granted", True)
                page.client_storage.set("storage_granted", True)
                await init_camera()
            else:
                state.update_status("❌ 权限被拒绝，无法使用相机")

        except Exception as e:
            logger.error(f"权限请求失败: {e}")
            state.update_status(f"权限错误: {str(e)}")

    async def init_camera():
        """初始化相机"""
        state.update_status("🔄 初始化相机中...")

        try:
            # 创建相机组件
            camera = create_camera_component()
            if not camera:
                state.update_status("❌ 相机初始化失败")
                return

            state.camera = camera
            camera_container.content = camera

            # 更新UI状态
            btn_start.disabled = True
            btn_capture.disabled = False
            btn_rotate.disabled = False
            state.is_camera_ready = True

            state.update_status("✅ 相机就绪 - 点击拍照按钮拍摄")

        except Exception as e:
            logger.error(f"相机初始化异常: {e}")
            state.update_status(f"❌ 初始化异常: {str(e)}")

    async def rotate_camera(e):
        """旋转相机预览"""
        if not state.camera:
            return

        state.rotation = (state.rotation + 90) % 360
        try:
            state.camera.rotate = state.rotation
            state.update_status(f"🔄 预览旋转: {state.rotation}°")
        except Exception as e:
            logger.warning(f"旋转不支持: {e}")
            state.update_status("⚠️ 该设备不支持旋转控制")

    async def capture_photo(e):
        """拍摄照片"""
        if not state.is_camera_ready or not state.camera:
            state.update_status("❌ 相机未就绪")
            return

        try:
            state.update_status("📸 拍摄中...")

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"FletPhoto_{timestamp}.jpg"
            save_path = os.path.join(get_storage_path(), filename)

            # 拍摄照片 - 使用同步版本避免兼容性问题
            success = state.camera.take_picture(save_path)

            if success and os.path.exists(save_path):
                # 更新预览
                preview_img = ft.Image(
                    src=save_path,
                    width=page.width * 0.9,
                    height=200,
                    fit=ft.ImageFit.CONTAIN,
                    border_radius=ft.border_radius.all(12),
                    error_content=ft.Text("预览加载失败")
                )

                preview_container.content = ft.Column([
                    ft.Text(f"最新拍摄: {filename}", size=14, weight=ft.FontWeight.BOLD),
                    preview_img
                ])

                state.last_captured_path = save_path
                state.update_status(f"✅ 照片已保存: {filename}")

                # 显示成功提示
                page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("照片保存成功!"),
                        action="确定",
                        duration=2000
                    )
                )
            else:
                state.update_status("❌ 照片保存失败")

        except Exception as e:
            logger.error(f"拍摄失败: {e}")
            state.update_status(f"❌ 拍摄错误: {str(e)}")

    async def open_gallery(e):
        """打开相册查看"""
        if state.last_captured_path and os.path.exists(state.last_captured_path):
            # 在移动设备上尝试用系统应用打开
            if page.platform == ft.Platform.ANDROID:
                # 这里可以集成原生功能
                state.update_status("📁 请到相册查看照片")
            else:
                state.update_status(f"照片位置: {state.last_captured_path}")
        else:
            state.update_status("暂无照片可查看")

    # UI组件 - 修复图标常量问题
    status_text = ft.Text(
        "请点击启动相机开始使用",
        size=16,
        weight=ft.FontWeight.W_500,
        color=ft.Colors.BLUE_GREY_700
    )

    btn_start = ft.ElevatedButton(
        "🚀 启动相机",
        on_click=check_permissions,
        icon=ft.Icons.CAMERA_ENHANCE,  # 修复：使用 ft.Icons
        height=50,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE_600,
            padding=ft.padding.symmetric(horizontal=20)
        )
    )

    btn_capture = ft.ElevatedButton(
        "📸 拍照",
        on_click=capture_photo,
        icon=ft.Icons.CAMERA_ALT,  # 修复
        height=50,
        disabled=True,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREEN_600,
            padding=ft.padding.symmetric(horizontal=20)
        )
    )

    btn_rotate = ft.OutlinedButton(
        "🔄 旋转",
        on_click=rotate_camera,
        icon=ft.Icons.SCREEN_ROTATION_ALT,  # 修复
        height=50,
        disabled=True
    )

    btn_gallery = ft.OutlinedButton(
        "🖼 查看",
        on_click=open_gallery,
        icon=ft.Icons.PHOTO_LIBRARY,  # 修复
        height=50
    )

    # 容器组件
    camera_container = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CAMERA_ALT, size=48, color=ft.Colors.GREY_400),  # 修复
            ft.Text("相机预览区域", size=16, color=ft.Colors.GREY_600)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=page.width,
        height=page.height * 0.6,
        padding=ft.padding.all(20),
        alignment=ft.alignment.center,
        border=ft.border.all(2, ft.Colors.GREY_300),
        border_radius=ft.border_radius.all(16),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.Colors.BLUE_GREY_50, ft.Colors.GREY_100]
        )
    )

    preview_container = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.PHOTO_SIZE_SELECT_ACTUAL, size=32, color=ft.Colors.GREY_400),  # 修复
            ft.Text("拍摄的照片将显示在这里", size=14, color=ft.Colors.GREY_600)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=page.width * 0.9,
        height=200,
        padding=ft.padding.all(16),
        alignment=ft.alignment.center,
        border=ft.border.all(1, ft.Colors.GREY_300),
        border_radius=ft.border_radius.all(12),
        bgcolor=ft.Colors.WHITE
    )

    # 组装页面
    page.add(
        ft.AppBar(
            title=ft.Text("Flet相机Demo", color=ft.Colors.WHITE),
            bgcolor=ft.Colors.BLUE_700,
            center_title=True,
            actions=[
                ft.IconButton(ft.Icons.INFO_OUTLINE, on_click=lambda _: page.show_dialog(  # 修复
                    ft.AlertDialog(
                        title=ft.Text("关于"),
                        content=ft.Text("Flet相机Demo v1.0\n基于Flet框架开发"),
                        actions=[ft.TextButton("确定", on_click=lambda _: page.close_dialog())]
                    )
                ))
            ]
        ),

        ft.Container(
            content=ft.Column([
                # 状态显示
                ft.Container(
                    content=status_text,
                    padding=ft.padding.symmetric(vertical=10),
                    alignment=ft.alignment.center
                ),

                # 相机预览区域
                camera_container,

                # 控制按钮组
                ft.Container(
                    content=ft.Row(
                        [btn_start, btn_capture],
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        spacing=10
                    ),
                    padding=ft.padding.symmetric(vertical=10)
                ),

                ft.Container(
                    content=ft.Row(
                        [btn_rotate, btn_gallery],
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        spacing=10
                    ),
                    padding=ft.padding.only(bottom=20)
                ),

                # 照片预览
                ft.Text("最近照片", size=16, weight=ft.FontWeight.BOLD),
                preview_container,

            ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.all(16),
            expand=True
        )
    )

    # 页面加载完成后的初始化
    async def on_page_load():
        # 检查之前是否已授权
        if (page.client_storage.get("camera_granted") and
                page.client_storage.get("storage_granted")):
            state.update_status("🔄 恢复相机会话...")
            await init_camera()

    page.on_load = on_page_load


if __name__ == "__main__":
    ft.app(target=main)