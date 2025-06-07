# `argv[0]`: Finding bugs in shadow-utils and util-linux

Command-line arguments and environment variables are forms of user input. Like any user input, they can be exploited by attackers. An attacker can manipulate `argc`, `argv`, and `envp` when considering local privilege escalation (LPE) attacks.

```c
int main(int argc, char *argv[], char *envp[]);
```

## pwnkit

On newer kernels ([linux-5.18+](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=1f6e5e2c)), Linux will not allow userspace programs to be called with `argc == 0` (it will silently fix this). However, on older Linux kernels, `argv[0]` can be `NULL`.

The reason this was changed was due to [PwnKit](https://blog.qualys.com/vulnerabilities-research/2022/01/25/cve-2021-4034-pkexec-local-privilege-escalation-vulnerability), a vulnerability in `pkexec`.

This was surprising to me, since `argv[0]` is usually defined as the running binary name. Almost all programs rely on `argv[0]` in usage messages/error messages.

In `pwnkit`, `pkexec` assumed that `argc` would be at least 1, which led to `argv` pointing out of bounds if `argc` was 0.

This was particularly bad for two reasons. The first is that `argv[argc+1]` is typically a pointer to `envp` in most Linux systems. The second is that `pwnkit` had argv rewriting code that ran after environment variable filtering code ran, resulting in code execution.

## Searching for similar vulnerabilities

To generate a list of potentially vulnerable targets, I ran every setuid program on my system with `argv[0]` pointing to `NULL` with the simple program below:

```c
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>

char* argv[] = {NULL};

int main(int argc, char** argv_real) {
    if (!argv_real[1]) {
        puts("Invalid arg");
    } else {
        printf("Calling %s", argv_real[1]);
        execve(argv_real[1], argv, 0);
    }
}
```

I discovered that when `argc == 0`, a few binaries inside of `shadow-utils` (`su`, `chsh`, etc.) can be forced to segfault since they were calling `basename` on `argv[0]` without checking if `argv[0]` is `NULL`. I reported the [issue](https://github.com/shadow-maint/shadow/issues/680) and wrote a quick [patch](https://github.com/shadow-maint/shadow/commit/c089196e15dcafc186474469c4914638da233b31).

Unlike in the `pkexec` case, it seems we don't have a way to exploit this bug. We can force a null dereference in a setuid program, but we can't gain any permissions or abilities.

## util-linux

One other potential security issue is that many binaries log `argv[0]` as the current program name.

In the case of su, `argv[0]` is sent to `/var/log/auth.log`. This allows us to hide our logs from other programs searching for `su`.

We can also include ANSI escape sequences as another method of attack:

```c
#include<stdio.h>
#include<unistd.h>
int main(int argc, char** my_argv){
        char* prog = "/usr/bin/su";
        char* argv[] = {"\033[33mYellow", "root", NULL};
        char* envp[] = {NULL};

        execve(prog, argv, envp);
        printf("Failed to exec\n");
}
```

Escape sequences can sometimes lead to code execution due to vulnerabilities in terminals. Terminal vulnerabilities have been found from [2003](https://seclists.org/fulldisclosure/2003/Feb/att-341/Termulation.txt) to [2024](https://packetstorm.news/files/id/177031).

I reported the issue and it was fixed in commit: [su, agetty: don't use program_invocation_short_name for openlog](https://git.kernel.org/pub/scm/utils/util-linux/util-linux.git/commit/?id=677a3168b261f3289e282a02dfd85d7f37de0447).

## Thanks

Many thanks to the shadow-utils and util-linux teams for their prompt responses and for merging the fix quickly. Their attention to detail and commitment to secure software is greatly appreciated.

---

**Commits:**
* [Fix null dereference in basename](https://github.com/shadow-maint/shadow/commit/c089196e15dcafc186474469c4914638da233b31)
* [su.c commit to disallow logging arbitrary strings](https://git.kernel.org/pub/scm/utils/util-linux/util-linux.git/commit/?id=677a3168b261f3289e282a02dfd85d7f37de0447)
* [Kernel commit to disallow `argc == 0`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=dcd46d897adb70d63e025f175a00a89797d31a43)

**References:**

* [Qualys PwnKit](https://blog.qualys.com/vulnerabilities-threat-research/2022/01/25/pwnkit-local-privilege-escalation-vulnerability-discovered-in-polkits-pkexec-cve-2021-4034)
* [My GitHub issue in shadow-utils](https://github.com/shadow-maint/shadow/issues/680)
* [LWN Article](https://lwn.net/Articles/882799/)
* [Terminal Command Injection 2003](https://seclists.org/fulldisclosure/2003/Feb/att-341/Termulation.txt)
* [Terminal Command Injection 2024](https://packetstorm.news/files/id/177031)
