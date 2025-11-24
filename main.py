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
    page.title = "Flet相机"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window_width = 400
    page.window_height = 700

    # 状态管理类
    class CameraState:
        def __init__(self):
            self.camera = None
            self.rotation = 0
            self.is_camera_ready = False
            self.last_captured_path = None

        def update_status(self, message):
            status_text.value = message
            page.update()

    state = CameraState()

    # 工具函数
    def get_storage_path():
        """
        获取存储路径
        注意：Android 10+ 有分区存储限制，直接写 DCIM 可能需要特殊权限或 MediaStore API。
        为了兼容性，这里优先使用 App 外部私有目录，该目录无需额外权限即可读写。
        """
        if page.platform == ft.Platform.ANDROID:
            # 尝试获取 Android 环境变量中的外部文件目录
            # 类似于: /storage/emulated/0/Android/data/com.example.fletcamera/files
            # 这是一个安全的写入位置
            try:
                # Flet 在 Android 上运行时，通常可以通过 os 模块访问这些路径
                # 但最安全的方式是使用相对路径，Flet 会将其解析到应用私有目录
                base_path = ""
            except:
                base_path = "photos"
        else:
            base_path = "photos"

        # 确保目录存在（如果是绝对路径）
        if base_path and not os.path.exists(base_path):
            try:
                Path(base_path).mkdir(parents=True, exist_ok=True)
            except:
                pass

        return base_path

    def create_camera_component():
        """创建相机组件"""
        try:
            return ft.Camera(
                expand=True,  # 让相机填满容器
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
            # 请求权限
            permissions = await page.request_permissions_async(
                [ft.PermissionType.CAMERA]
            )

            # 在 Flet 0.24+ 中，权限处理逻辑可能略有不同，这里简化处理
            # 实际上初始化相机时，系统通常也会自动弹窗
            await init_camera()

        except Exception as e:
            logger.error(f"权限请求失败: {e}")
            state.update_status(f"权限错误: {str(e)}")

    async def init_camera():
        """初始化相机"""
        state.update_status("🔄 初始化相机中...")

        try:
            camera = create_camera_component()
            if not camera:
                state.update_status("❌ 相机初始化失败")
                return

            state.camera = camera
            camera_container.content = camera

            btn_start.disabled = True
            btn_capture.disabled = False
            btn_rotate.disabled = False
            state.is_camera_ready = True

            state.update_status("✅ 相机就绪")
            page.update()

        except Exception as e:
            logger.error(f"相机初始化异常: {e}")
            state.update_status(f"❌ 初始化异常: {str(e)}")

    async def rotate_camera(e):
        """旋转相机预览"""
        if not state.camera:
            return

        # 注意：Flet Camera 目前并未完全支持所有设备的 rotate 属性实时热更新
        # 但我们可以尝试切换摄像头 ID (0: 后置, 1: 前置)
        state.rotation = (state.rotation + 1) % 2
        try:
            state.camera.camera_id = state.rotation
            state.update_status(f"🔄 切换摄像头: {'前置' if state.rotation else '后置'}")
            page.update()
        except Exception as e:
            state.update_status("⚠️ 切换失败")

    async def capture_photo(e):
        """拍摄照片"""
        if not state.is_camera_ready or not state.camera:
            state.update_status("❌ 相机未就绪")
            return

        try:
            state.update_status("📸 拍摄中...")
            page.update() // 强制刷新UI

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"IMG_{timestamp}.jpg"

            # 使用相对路径，Flet 会自动处理
            # 在 Android 上，这通常位于 /data/user/0/包名/app_flutter/ 或类似的内部私有目录
            save_path = filename

            # 异步拍摄
            await state.camera.take_picture_async(save_path)

            # 稍微等待一下文件写入
            import asyncio
            await asyncio.sleep(0.5)

            state.last_captured_path = save_path

            # 更新预览
            preview_img = ft.Image(
                src=save_path,  # Flet 可以直接读取相对路径的图片
                width=page.width * 0.9,
                height=200,
                fit=ft.ImageFit.CONTAIN,
                border_radius=ft.border_radius.all(12)
            )

            preview_container.content = ft.Column([
                ft.Text(f"已保存: {filename}", size=14),
                preview_img
            ])

            state.update_status("✅ 拍摄成功")
            page.update()

        except Exception as e:
            logger.error(f"拍摄失败: {e}")
            state.update_status(f"❌ 错误: {str(e)}")

    # UI组件
    status_text = ft.Text("请点击启动相机", size=16, color=ft.Colors.BLUE_GREY_700)

    btn_start = ft.ElevatedButton(
        "启动相机", on_click=check_permissions, icon=ft.Icons.CAMERA_ENHANCE,
        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE)
    )

    btn_capture = ft.ElevatedButton(
        "拍照", on_click=capture_photo, icon=ft.Icons.CAMERA_ALT, disabled=True,
        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE)
    )

    btn_rotate = ft.IconButton(icon=ft.Icons.SWITCH_CAMERA, on_click=rotate_camera, disabled=True)

    camera_container = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CAMERA_ALT, size=48, color=ft.Colors.GREY_400),
            ft.Text("预览区域", color=ft.Colors.GREY_600)
        ], alignment=ft.MainAxisAlignment.CENTER),
        width=page.width,
        height=page.height * 0.5,
        border=ft.border.all(1, ft.Colors.GREY_300),
        border_radius=10,
        bgcolor=ft.Colors.BLACK12,
        clip_behavior=ft.ClipBehavior.HARD_EDGE  # 确保画面不溢出
    )

    preview_container = ft.Container(
        content=ft.Text("暂无照片"),
        padding=10,
        alignment=ft.alignment.center,
        border=ft.border.all(1, ft.Colors.GREY_200),
        border_radius=10
    )

    page.add(
        ft.AppBar(title=ft.Text("Flet相机"), bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
        ft.Column([
            ft.Container(content=status_text, alignment=ft.alignment.center, padding=10),
            camera_container,
            ft.Row([btn_start, btn_capture, btn_rotate], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            ft.Divider(),
            preview_container
        ], scroll=ft.ScrollMode.AUTO, expand=True)
    )


if __name__ == "__main__":
    ft.app(target=main)