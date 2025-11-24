import flet as ft
from datetime import datetime
import asyncio
import traceback


def main(page: ft.Page):
    # 错误捕获兜底，防止白屏
    try:
        page.title = "Flet 终极相机"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 20
        page.bgcolor = ft.Colors.WHITE
        page.window_width = 400
        page.window_height = 800

        # --- 状态管理 ---
        class AppState:
            camera = None
            permission_granted = False

        state = AppState()

        # --- UI 组件 ---
        status_text = ft.Text("系统就绪，请启动相机", color=ft.Colors.BLUE_GREY_700)
        preview_image = ft.Image(visible=False, height=200, fit=ft.ImageFit.CONTAIN)

        # --- 核心逻辑 ---

        async def init_camera():
            try:
                status_text.value = "正在初始化相机..."
                status_text.update()

                await asyncio.sleep(0.5)

                # Flet 0.22.1 相机控件
                state.camera = ft.Camera(
                    expand=True,
                    fit=ft.ImageFit.COVER,
                    visible=True
                )

                camera_box.content = state.camera
                camera_box.update()

                btn_start.visible = False
                btn_capture.disabled = False
                page.update()

                status_text.value = "✅ 相机运行中"
                status_text.update()

            except Exception as ex:
                status_text.value = f"初始化失败: {ex}"
                status_text.update()

        # 权限回调
        def on_permission_result(e):
            print(f"权限结果: {e.status}")
            if e.status == ft.PermissionStatus.GRANTED:
                state.permission_granted = True
                page.run_task(init_camera)
            else:
                status_text.value = f"❌ 需要相机权限: {e.status}"
                status_text.update()

        # --- 关键修复点 ---
        # 1. 先创建对象（不传参，避免你本地新版 Flet 报错）
        try:
            perm_handler = ft.PermissionHandler()
        except TypeError:
            # 极低概率兜底：如果版本极旧需要传参（不太可能，但为了保险）
            perm_handler = ft.PermissionHandler(on_status_change=on_permission_result)

        # 2. 后赋值属性（所有版本都支持这种写法）
        perm_handler.on_status_change = on_permission_result

        # 3. 添加到 overlay
        page.overlay.append(perm_handler)

        # 按钮事件
        def start_click(e):
            status_text.value = "正在请求权限..."
            status_text.update()
            try:
                perm_handler.request_permission(ft.PermissionType.CAMERA)
            except Exception as ex:
                status_text.value = f"请求失败: {ex}"
                status_text.update()

        async def capture_click(e):
            if not state.camera:
                return

            try:
                status_text.value = "📸 拍照中..."
                status_text.update()

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"IMG_{timestamp}.jpg"

                await state.camera.take_picture_async(filename)

                await asyncio.sleep(0.5)

                preview_image.src = filename
                preview_image.visible = True
                preview_image.src += f"?v={timestamp}"

                status_text.value = f"已保存: {filename}"
                page.update()

            except Exception as ex:
                status_text.value = f"拍照错误: {ex}"
                status_text.update()

        # --- UI 布局 ---
        camera_box = ft.Container(
            content=ft.Icon(ft.Icons.CAMERA_ALT, size=50, color=ft.Colors.GREY_300),
            height=300,
            bgcolor=ft.Colors.BLACK12,
            border_radius=10,
            alignment=ft.alignment.center
        )

        btn_start = ft.ElevatedButton("启动相机", on_click=start_click, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE)
        btn_capture = ft.ElevatedButton("拍照", on_click=capture_click, disabled=True, bgcolor=ft.Colors.GREEN,
                                        color=ft.Colors.WHITE)

        page.add(
            ft.Column([
                ft.Text("Flet 修复版相机", size=20, weight=ft.FontWeight.BOLD),
                status_text,
                ft.Divider(),
                camera_box,
                ft.Container(height=10),
                ft.Row([btn_start, btn_capture], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(),
                preview_image
            ])
        )

    except Exception as e:
        page.clean()
        page.add(ft.Text(f"致命错误: {traceback.format_exc()}", color=ft.Colors.RED))


if __name__ == "__main__":
    ft.app(target=main)