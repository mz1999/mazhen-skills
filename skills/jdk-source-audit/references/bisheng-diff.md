# 毕昇 JDK 差异识别

**默认假设**：机制在 OpenJDK 同版本源码中存在完全相同的代码 → 视为 OpenJDK 通用逻辑；只有毕昇独有的才标注为特有优化。

判断方法：
- 检查文件头部 Copyright 声明——是否有华为/毕昇的版权行。
- 查 git history，看该文件/函数是否由华为提交、或是否有 `bisheng`/`huawei` 相关 commit。
- 对比 OpenJDK 上游同版本：若代码完全一致，按 OpenJDK 通用逻辑讲；若有差异，单独标注为毕昇特有，并说明改了什么、为什么（查 commit message）。
