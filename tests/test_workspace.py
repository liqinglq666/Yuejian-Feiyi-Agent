from ui.workspace import apply_example


def test_apply_example_updates_widget_state_before_render() -> None:
    state = {
        "selected_scene": "游客路线",
        "user_input": "旧内容",
    }

    apply_example(state, "内容创作", "介绍潮汕英歌舞")

    assert state["selected_scene"] == "内容创作"
    assert state["user_input"] == "介绍潮汕英歌舞"
