import flet as ft
from datetime import datetime
import os
import logging
import asyncio

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(page: ft.Page):
    page.title = "Flet相机"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window_width = 400
    page.window_height = 700

    # 状态持有
    class AppState:
        camera = None
        is_ready = False

    state = AppState()

    # UI 状态更新辅助
    def update_status(msg):
        status_text.value = msg
        status_text.update()

    # --- 核心逻辑 ---

    def create_camera():
        """创建相机控件"""
        return ft.Camera(
            expand=True,
            fit=ft.ImageFit.COVER,
            visible=True
        )

    async def init_camera():
        """权限获取成功后，执行此函数初始化相机"""
        try:
            update_status("权限已获取，正在启动相机...")

            cam = create_camera()
            camera_container.content = cam
            camera_container.update()
            state.camera = cam
            state.is_ready = True

            # 更新按钮状态
            btn_start.disabled = True
            btn_capture.disabled = False
            btn_start.update()
            btn_capture.update()

            update_status("✅ 相机已就绪，请拍照")

        except Exception as e:
            update_status(f"❌ 启动失败: {e}")

    # --- 权限处理逻辑 (修复报错的核心部分) ---

    def on_permission_result(e):
        """权限请求的回调结果"""
        logger.info(f"Permission result: {e.permission} - {e.status}")

        # Flet 的 PermissionStatus 枚举：GRANTED, DENIED, etc.
        if e.status == ft.PermissionStatus.GRANTED:
            # 权限被允许，开始初始化
            page.run_task(init_camera)
        else:
            update_status("❌ 必须授予相机权限才能使用！")

    # 创建权限处理器控件
    permission_handler = ft.PermissionHandler(on_status_change=on_permission_result)
    # 重要：必须添加到页面 overlay 中才能工作
    page.overlay.append(permission_handler)

    async def request_camera_permission(e):
        """点击启动按钮触发"""
        update_status("正在请求权限...")
        # 发起请求，结果会回调 on_permission_result
        permission_handler.request_permission(ft.PermissionType.CAMERA)

    async def capture_photo(e):
        """拍照逻辑"""
        if not state.is_ready or not state.camera:
            return

        try:
            update_status("📸 拍摄中...")

            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"IMG_{timestamp}.jpg"
            # Android 推荐使用相对路径，Flet 会自动处理到应用私有目录
            save_path = filename

            await state.camera.take_picture_async(save_path)

            # 延迟一小会儿确保文件写入
            await asyncio.sleep(0.5)

            # 更新预览
            preview_img.src = save_path
            # 添加一个随机参数强制刷新图片缓存
            preview_img.src += f"?v={timestamp}"
            preview_text.value = f"已保存: {filename}"

            preview_container.update()
            update_status("✅ 拍摄成功")

        except Exception as e:
            logger.error(f"Error: {e}")
            update_status(f"❌ 拍摄出错: {e}")

    # --- UI 构建 ---

    status_text = ft.Text("点击下方按钮启动相机", color=ft.Colors.GREY_700)

    camera_container = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CAMERA_ALT, size=50, color=ft.Colors.GREY_300),
            ft.Text("相机预览区域", color=ft.Colors.GREY_400)
        ], alignment=ft.MainAxisAlignment.CENTER),
        expand=True,
        bgcolor=ft.Colors.BLACK87,
        alignment=ft.alignment.center
    )

    preview_img = ft.Image(
        src="",
        visible=True,
        height=150,
        fit=ft.ImageFit.CONTAIN
    )
    preview_text = ft.Text("暂无照片")

    preview_container = ft.Column([
        preview_text,
        preview_img
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    btn_start = ft.ElevatedButton(
        "🚀 启动相机",
        on_click=request_camera_permission,  # 绑定到修复后的函数
        bgcolor=ft.Colors.BLUE,
        color=ft.Colors.WHITE
    )

    btn_capture = ft.ElevatedButton(
        "📸 拍照",
        on_click=capture_photo,
        disabled=True,
        bgcolor=ft.Colors.GREEN,
        color=ft.Colors.WHITE
    )

    # 页面布局
    page.add(
        ft.Column([
            ft.Container(status_text, padding=10, alignment=ft.alignment.center),
            ft.Container(camera_container, expand=True, border_radius=10, margin=10),
            ft.Container(
                content=ft.Row([btn_start, btn_capture], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                padding=10
            ),
            ft.Container(preview_container, height=200, bgcolor=ft.Colors.GREY_100, border_radius=10, padding=10)
        ], expand=True)
    )


if __name__ == "__main__":
    ft.app(target=main)