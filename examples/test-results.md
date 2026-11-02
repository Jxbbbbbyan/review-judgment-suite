# Test results / 测试结果

Date / 日期：2026-11-02. Scope: local package and synthetic fixtures. No live preset activation, deployment, network API execution or Grok submission was performed.

## Automated regression / 自动回归

Command / 命令：`python -m unittest discover -s tests -v`

Final observed output / 最终真实输出：**`Ran 23 tests ... OK`**. The interpreter was an installed Python 3.13 runtime; Python 3.10+ is the source-level requirement, but this run does not establish a tested platform/version matrix.

初版 18 项中有一项测试把小数传给整数 timeout 参数，测试本身报错；改为合法的整数超时后通过。之后独立审查复现了三处过程漏洞，均已修复并增加回归；另外补了不改内容却反复重开审查的轮次检查，以及旧 Nit 编号被复用的检查，最终为 23 项。

The initial 18-test run exposed a test-input mismatch: a fractional timeout was supplied to an integer CLI option. After correction, the suite passed. Independent review then reproduced three coordinator defects; repairs and regression cases were added, along with unchanged-content round limits and historical ID reuse coverage. Final count: 23 tests.

| Reproduced coordinator issue / 组合脚本问题 | Repair / 修复 | Regression evidence / 回归证据 |
|---|---|---|
| Reused IDs could overwrite prior Important obligations / 重复编号覆盖旧问题 | Global finding-ID registry; old issues referenced separately | Duplicate Important and prior-Nit ID tests |
| A route could reuse an old resolution / 回退后沿用旧处置 | Clear current resolutions when dependent gates invalidate | Re-adjudication and retained-obligation tests |
| Changed source could reopen a closed run / 源文件变化重开结束状态 | Check terminal/closed before refresh; keep historical snapshot | Closed-run source-change test |

Skill structural validation also returned **`Skill is valid!`**. On the first attempt, the external validator read UTF-8 text with a GBK default; rerunning it with UTF-8 mode succeeded. This environment correction did not modify the validator or weaken the skill rules.

## Independent code review / 独立代码审查

Round 1: **3 Important, 0 Nit, 0 Pre-existing**; each had a reproduced failure. Round 2 after repairs: **0 Important, 0 Nit, 0 Pre-existing**. The independent reviewer reran the 23 tests and additionally checked that all five route targets clear stale dispositions, check/risk re-entry advances the round, and an over-budget route preserves the remaining token count.

风险为 Medium，因为这是可被复用的过程门与打包脚本。最终结论是“可交付本地审阅包”，不是“已经获得人工批准并激活”。没有修改原技能、共享 persona 或安装配置。实际审批真实性、独立上下文和检查充分性仍需宿主及使用者负责。

Risk is Medium. The outcome is a reviewable local package, not an assertion of human approval or live activation. Original skills, shared personas and host installation settings were not changed.

## Fresh-context forward trial / 新上下文前向试用

The reviewer received only the packaged skill, the synthetic [requirements](forward-task/REQUIREMENTS.md) and [source](forward-task/ratio.py). It did not read the author's regression suite or implementation rationale. Its independently written [contract checker](forward-contract-check.py) is included for reproduction:

```powershell
python examples/forward-contract-check.py examples/forward-task/ratio.py
```

**Expected result for this intentionally broken fixture: exit 1, `Ran 7 tests`, `FAILED (failures=2, errors=1)`**. This is a negative fixture kept unchanged to demonstrate refusal gates; do not treat it as a production utility or a failed package regression.

独立 reviewer 发现并复现两类问题：全零输入除零；负数输入没有按契约抛 ValueError。7 个检查中 4 个通过、2 个失败、1 个错误。失败原始记录被保留，完成失败归因后，risk/review/close 仍拒绝继续，最终 handoff。

A second, separate run used a genuine syntax-only check, explicitly labelled as having no behavioural coverage. It imported the reviewer's two Important findings, then `close` returned exit 2 for unresolved Important. The first failed run was neither deleted nor replaced. No source fix, rejection or human approval was fabricated.

两个运行的前后内容快照一致，源代码未改。试用还记录了一处操作摩擦：从项目外传相对 owner 路径时，路径按调用目录解析，首次 init 拒绝；改为实际可读的绝对路径后成功。CLI 文档已补充这条路径规则。

Snapshots remained unchanged across the trial. An operator initially passed a project-relative owner path from outside the project; the CLI resolves owner paths from the caller's directory, so init rejected it. The corrected absolute readable path worked. This is documented usage behaviour, not a hidden successful attempt.

## Earlier observed workflow / 打包前已有的工作流

[The prior case](prior-independent-review.md) is separately redacted from the preceding real author/reviewer task. It reports historical observations rather than a run of this new coordinator. Raw conversation IDs, usernames, project URLs, absolute private paths and submission identifiers were removed. Raw local trial state and approval material are not included in the archive.

## What these tests do not prove / 尚未证明的部分

The tests establish the observed gates and outputs for these inputs. They do not establish review recall/precision, better model judgment, reduced cost, universally safe command execution, or authenticated reviewer/human identity. There is no cross-host or cross-model controlled study. The included scripts do not supply a sandbox, a model backend or automatic agent scheduling.
