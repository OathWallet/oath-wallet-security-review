/* Exercise pinned upstream rand.c with injected operating-system failures.
 * Synthetic bytes test error handling, not entropy quality or binary identity. */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/resource.h>
#include <TrezorCrypto/rand.h>
static int mode, opened, closed;
int entropy_open(const char *path, int flags, ...) {
    (void)flags;
    if (strcmp(path, "/dev/urandom") != 0) _exit(91);
    opened++;
    return mode == 1 ? -1 : 123;
}
ssize_t entropy_read(int fd, void *buffer, size_t count) {
    if (fd != 123) _exit(92);
    if (mode == 2) return -1;
    memset(buffer, 0xa5, count);
    return mode == 3 ? (ssize_t)count - 1 : (ssize_t)count;
}
int entropy_close(int fd) { if (fd != 123) _exit(93); closed++; return 0; }
static int failure(int scenario, int scalar) {
    pid_t child = fork();
    if (child < 0) return 1;
    if (child == 0) {
        struct rlimit limit = {0, 0}; setrlimit(RLIMIT_CORE, &limit);
        mode = scenario;
        if (scalar) (void)random32(); else { uint8_t bytes[32]; random_buffer(bytes, sizeof bytes); }
        _exit(90); /* A failure must not return possibly predictable bytes. */
    }
    int status;
    if (waitpid(child, &status, 0) != child) return 1;
    return !(WIFSIGNALED(status) && WTERMSIG(status) == SIGABRT);
}
int main(void) {
    int errors = 0;
    uint8_t bytes[32]; random_buffer(bytes, sizeof bytes);
    for (size_t i = 0; i < sizeof bytes; i++) errors += bytes[i] != 0xa5;
    errors += random32() != UINT32_C(0xa5a5a5a5);
    errors += opened != 2 || closed != 2;
    for (int scenario = 1; scenario <= 3; scenario++)
        for (int scalar = 0; scalar <= 1; scalar++) errors += failure(scenario, scalar);
    printf("Upstream entropy failure handling: 8 scenarios, %d failures\n", errors);
    return errors ? 1 : 0;
}
