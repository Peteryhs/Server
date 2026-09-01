# Hermes

Documentation / Guide on my centralized Hermes setup.

This setup converts your Hermes instance from an assistant on one computer to a 24/7 entity that can act on every device in the fleet, as long as that device is online.

When an agent like Hermes runs on one computer, it is practically confined to it. You open the app on your laptop, you chat, it helps with what is on that laptop. When you close it, nothing happens without you. This setup is the opposite. Hermes runs on its own always-on machine, and it is not tied to any one device.

With the following setup, Hermes becomes:

1. **Always on.** The machine never sleeps, so Hermes never sleeps. It answers from anywhere, at any time, through the desktop app or Matrix.
2. **Works across devices.** Hermes can work across all of your devices, on the Linux desktop, on the Windows laptop, and on the server. You sit at one screen, Hermes makes all of the information come to you. No more "I need to grab this file from my other machine".
3. **One history, one memory.** Every chat on every device goes through this one instance. There is a single conversation history and a single memory store, synced to all machines through the Obsidian vault.
4. **Works while you are away.** Work can be queued for a device that is offline. Every 15 minutes a watchdog checks the fleet, and the queued work runs on its own when the device comes back online.

This allows it to achieve one important point: Hermes is there even when you are not.

The above is achieved by putting all of the machines into one tailnet, then running Hermes on a dedicated machine in that tailnet, then granting SSH access from the Hermes instance to all other machines, plus some smaller setups.

## Setup guide

1. Ensure you have the Hermes Desktop app on all of the devices you want to control. 
2. Create a Tailscale account at https://login.tailscale.com.
3. Install the Tailscale VPN client on all of the affected devices. There is a client for almost anything.
	1. Only the devices with the Hermes desktop app need it, you do not need it on your phone.
4. Log all clients into your Tailscale account and make sure the VPN is connected, so all devices show "online" in your Tailscale dashboard.
5. Install OpenSSH on all of the devices Tailscale is on.
6. Pick the dedicated Hermes device. This is the one machine that stays online all the time and runs the Hermes instance that every other device connects to:
	1. Use a device you do not need to move or turn off: a spare desktop, an old laptop left plugged in, or a small server all work.
	2. Disable sleep and automatic shutdown on it, or Hermes goes offline with it.
	3. It does not need to be powerful. The real work happens on the devices it reaches over SSH, so a modest always-on machine is enough.
	4. Complete the full Hermes setup on this device before moving on.
7. Grant Hermes SSH access to every device.

## Granting Hermes SSH access

To act on a device, Hermes needs its SSH key on that device. Granting access means putting the public key into the target device's `authorized_keys`.

### Getting the public key

The key is generated once on the Hermes device. If it does not exist yet, create it:

```
ssh-keygen -t ed25519
```

This creates the private key at `~/.ssh/id_ed25519` and the public key at `~/.ssh/id_ed25519.pub`. Hermes uses the private key to log in. The public key is the part you give to other devices.

Print the public key whenever you need to grant it:

```
cat ~/.ssh/id_ed25519.pub
```

Never share the private key, the file without the `.pub` extension. It stays on the Hermes device only.

### Linux devices

1. Print the public key on the Hermes machine (see Getting the public key above).
2. Append the line to `~/.ssh/authorized_keys` in the target user's home on that device. On most setups `ssh-copy-id <user>@<hostname>` does this for you.
3. Make sure the file is private: `chmod 600 ~/.ssh/authorized_keys`
4. Verify from the Hermes machine: `ssh <user>@<hostname> 'hostname'`

### Windows laptop

1. Enable OpenSSH Server on Windows: Settings > Apps > Optional Features > OpenSSH Server, then start the `sshd` service.
2. Put the public key in `C:\Users\<user>\.ssh\authorized_keys`.
3. If the account is an administrator, use `C:\ProgramData\ssh\administrators_authorized_keys` instead, and restrict its ACL to Administrators and SYSTEM. Windows silently ignores a key in the wrong place, so verify after granting.

### Notes

- The key is a master key. It can log into every device that holds it, so only add devices you trust.
- `ssh-copy-id <user>@<hostname>` copies the public key to a Linux device in one step.
- You can probably just tell Hermes to grab the keys for you and enter them in. For the sake of privacy the manual steps are here.

## Getting Hermes to know the devices

After you have copied the public key to all of the devices, ask the centralized Hermes instance to try to SSH into the machines that are connected over Tailscale. It should be able to log into all of them.

It is highly recommended that you describe the use case of each machine to Hermes, so it remembers which machine is which based on its IP and Tailscale name.

For instance, my Hermes instance understands entries like this (a template, fill in with your own machines):

```
[tailscale IP] -> [tailscale name] -> [what you use this machine for]
```

This way, when you need work done on a specific machine, Hermes can pinpoint it and SSH in directly.

**Optional** Helper:  `active-device`, a small script on the Hermes machine. It reads the live connections to the gateway and maps each tailnet IP back to a device name, so Hermes knows which device you are talking to it from right now. That matters when the same question needs a different answer depending on the device. Script: [scripts/hermes](https://github.com/Peteryhs/Server/tree/main/scripts/hermes).

Setup: send the script to your Hermes agent and ask it to install it on the Hermes machine and call it whenever it needs to know which device you are on.

At this point you should have a quite capable Hermes agent, able to help you on any of the devices over SSH.

> [!note]- Story time
> Recently I was fully locked out of my Fedora system because the system GUI was completely bugged, and I could not interact with any GUI elements, including the emergency terminal. I contacted Hermes via my phone, and SSH still worked. Hermes researched the issue, figured out that I had broken the desktop environment with tweaks the day before, applied the fix, and opened a GUI terminal for me to restart.
>
> This could have been fixed manually by SSHing into the device, but I was going to be out the entire day. Having everything fixed from my phone while eating breakfast was an absolute godsend.

However, there is much more work to do to make it better. On to the next section.

## Watchdog and queued work

Hermes can do work on a device even when you are gone. Drop a task into the queue and the watchdog takes it from there.

- Queue: tasks are queued as markdown files in a per-device folder on the Hermes machine.
- Watchdog: [fleet-online.sh](https://github.com/Peteryhs/Server/tree/main/scripts/hermes), a script that runs on a schedule (cron), once every 15 minutes.
- The watchdog checks a device's reachability over SSH. A device only becomes actionable once its SSH key is granted, which is why key setup comes first.

The watchdog emits one of three states per device:

| State | Meaning | Does anything happen |
|---|---|---|
| IDLE | No queued tasks | No |
| WAITING | Tasks queued, device offline | No |
| READY[-N] | Tasks queued, device online | Yes, the task runs |

A failed task bumps the retry counter, so stuck work wakes the watchdog again instead of parking silently. The script keeps its output stable, so the cron job only wakes Hermes when a state actually changes.

Setup: send the script to your Hermes agent and ask it to install it on the Hermes machine and wire it up as a cron job that runs every 15 minutes.

## Memory and history

- **One history.** All chats route through this gateway, so there is one conversation history no matter which device you used.
- **One memory.** Memory and skills are stored on this machine and mirrored through Obsidian LiveSync into the vault. Every device sees the same memory.
- The vault must sync before Hermes starts on any machine, or that machine reads stale memory.

## Reach and limits

This setup gives Hermes real reach over the fleet. Being honest about it:

- The SSH master key is full access to every granted device. Grant it only where you mean it.
- A device must be online for actions. Offline work waits in the queue.
- The Windows laptop gateway stays disabled, or every Matrix message comes twice.