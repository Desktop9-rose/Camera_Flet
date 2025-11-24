import flet as ft
from datetime import datetime
import asyncio
import traceback  # 用于显示详细报错


def main(page: ft.Page):
    # 全局错误捕获：防止白屏
    try:
        # --- 1. 基础页面设置 ---
        page.title = "Flet相机"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 10
        page.scroll = ft.ScrollMode.AUTO
        page.bgcolor = ft.Colors.WHITE

        # --- 2. 状态管理 ---
        class AppState:
            camera = None

        state = AppState()

        # UI 组件引用
        status_text = ft.Text("准备就绪", color=ft.Colors.BLUE_GREY_700)
        preview_image = ft.Image(visible=False, height=200, fit=ft.ImageFit.CONTAIN)

        # --- 3. 核心功能函数 ---

        # 权限回调处理
        def on_permission_result(e):
            if e.status == ft.PermissionStatus.GRANTED:
                status_text.value = "✅ 权限已获取，正在启动相机..."
                status_text.update()
                # 权限允许后，异步启动相机
                page.run_task(init_camera_task)
            else:
                status_text.value = f"❌ 权限被拒绝: {e.status}"
                status_text.update()

        # 创建权限处理器
        perm_handler = ft.PermissionHandler(on_status_change=on_permission_result)
        page.overlay.append(perm_handler)

        # 异步启动相机任务
        async def init_camera_task():
            await asyncio.sleep(0.5)  # 给UI一点缓冲
            try:
                state.camera = ft.Camera(
                    expand=True,
                    fit=ft.ImageFit.COVER,
                    visible=True
                )
                camera_container.content = state.camera
                camera_container.update()

                btn_start.disabled = True
                btn_capture.disabled = False
                page.update()
                status_text.value = "📷 相机运行中"
                status_text.update()
            except Exception as ex:
                status_text.value = f"启动相机失败: {ex}"
                status_text.update()

        # 按钮事件
        def request_perms(e):
            status_text.value = "正在请求系统权限..."
            status_text.update()
            perm_handler.request_permission(ft.PermissionType.CAMERA)

        async def capture_photo(e):
            if not state.camera:
                return

            status_text.value = "📸 正在拍照..."
            status_text.update()

            try:
                # 生成文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"IMG_{timestamp}.jpg"

                # 拍照
                await state.camera.take_picture_async(filename)

                # 等待文件写入
                await asyncio.sleep(0.5)

                # 更新预览
                preview_image.src = filename
                preview_image.visible = True
                # 强制刷新缓存
                preview_image.src += f"?v={timestamp}"

                status_text.value = f"✅ 已保存: {filename}"
                page.update()

            except Exception as ex:
                status_text.value = f"❌ 拍照错误: {ex}"
                page.update()

        # --- 4. UI 布局 ---

        camera_container = ft.Container(
            content=ft.Column(
                [ft.Icon(ft.Icons.CAMERA_ALT, size=40, color=ft.Colors.GREY_300)],
                alignment=ft.MainAxisAlignment.CENTER
            ),
            height=300,
            bgcolor=ft.Colors.BLACK12,
            border_radius=10,
            alignment=ft.alignment.center,
        )

        btn_start = ft.ElevatedButton("启动相机 (请求权限)", on_click=request_perms, bgcolor=ft.Colors.BLUE,
                                      color=ft.Colors.WHITE)
        btn_capture = ft.ElevatedButton("拍照", on_click=capture_photo, disabled=True, bgcolor=ft.Colors.GREEN,
                                        color=ft.Colors.WHITE)

        page.add(
            ft.Text("Flet 相机诊断版", size=20, weight=ft.FontWeight.BOLD),
            status_text,
            ft.Divider(),
            camera_container,
            ft.Row([btn_start, btn_capture], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            ft.Divider(),
            ft.Text("照片预览:"),
            preview_image
        )

    except Exception as e:
        # --- 致命错误捕获 ---
        # 如果上面任何代码导致崩溃，这里会显示错误堆栈，而不是白屏
        page.clean()
        page.add(
            ft.Text("⚠️ 程序发生致命错误", color=ft.Colors.RED, size=24),
            ft.Text(f"错误详情:\n{traceback.format_exc()}", color=ft.Colors.RED_900, font_family="monospace")
        )
        page.update()


if __name__ == "__main__":
    ft.app(target=main)