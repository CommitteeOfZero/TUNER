# TUNER

### Transplant Utilizing Native Executable Reference (TUNER): a Kaleido ADV Workshop conversion framework

**Prerequisites:**
- Python 3.7+
- The PC executable of *Kono Subarashii Sekai ni Shukufuku o! -Kono Yokubukai Game ni Shinpan o!-*
- A decrypted game dump of *OCCULTIC;NINE* for the PS4, ~~PS Vita, or Xbox One~~
- Enough storage space to hold presumably multiple copies of the game you want to convert

Note: *Kono Subarashii Sekai ni Shukufuku o! -Kono Yokubukai Game ni Shinpan o!-*, also known as *Konosuba: Judgment on this Greedy Game!*, can only be purchased through the [DMM storefront](https://dlsoft.dmm.com/detail/images_0013/), which may necessitate usage of a VPN set to a Japanese region. This game is not to be confused with *Kono Subarashii Sekai ni Shukufuku o! ~Kono Yokubou no Ishou ni Chouai o!~*, also known as *KONOSUBA - God's Blessing on this Wonderful World! Love For These Clothes Of Desire!*, which exists within a completely different game engine.

Please do not mistakenly download the source code of this project when attempting to use it. Download the relevant release to the side.

Place your *OCCULTIC;NINE* game files and `KONOSUBA.exe` in the `FILES_GO_HERE` directory.
With a PS4 ~~or PSV~~ dump, these files will originate from the `windata` folder.
~~With an XB1 dump, these files will originate from the `Mount` folder.~~

**Necessary *OCCULTIC;NINE* files:**
- `config_body.bin`
- `config_info.psb.m`
- `eboot.bin` (for PS4 dumps)
- `eboot.bin.elf` (for PSV dumps)
- `advengine.exe` (for XB1 dumps)
- `font_body.bin`
- `font_info.psb.m`
- `image_body.bin`
- `image_info.psb.m`
- `motion_body.bin`
- `motion_info.psb.m`
- `scenario_body.bin`
- `scenario_info.psb.m`
- `script_body.bin`
- `script_info.psb.m`
- `sound_body.bin`
- `sound_info.psb.m`
- `voice_body.bin`
- `voice_info.psb.m`
- `movie` (folder), containing:
`ED_BAD.mp4`
`ED_NORMAL.mp4`
`ED_TRUE.mp4`
`Intro.mp4`
`OP.mp4`

To avoid publishing cryptographic keys within this conversion kit, obtaining these keys is done at the beginning of the conversion process by referencing addresses within the provided files. If you don't know what that means, that's fine. All you probably need to know is the next part.

Once all files are in place and you have run `convert.bat`, it should produce a fully operational OCCULTIC;NINE PC port within the `OUTPUT` folder. This process may take a significant amount of time, as it has to unpack the entirety of *OCCULTIC;NINE*, make several thousands upon thousands of text adjustments and audio/video conversions, and then repack any relevant archives.

**Credit to the handy tools in the releases:**
- [FreeMote Toolkit](https://github.com/UlyssesWu/FreeMote) - file unpacking/repacking
- [FFmpeg-Builds-Win32](https://github.com/defisym/FFmpeg-Builds-Win32) - video conversion
- [rcedit](https://github.com/electron/rcedit) - swapping exe icon
- xWMAEncode - converting audio

All of these, as well as the game itself, should be functional on x86 systems.

An extremely special, massive, infinite, never-ending thanks to [MrComputerRevo](https://github.com/MrComputerRevo) for his initial attempt, *OcculticKonosuba*, whose project output was used as a point of comparison alongside direct commentary on the process behind the conversion.
And of course, [Tea](https://github.com/BoilingTeapot), for their own insight bordering on wizardry. 

**Known issues:**
- Partly or entirely crackly audio, immediately evident upon entering the title screen. Restarting the game usually remedies this for the session, though if occurring unavoidably no matter what, re-running TUNER may be necessary.
- No innate ability to pause the game or interact with certain gameplay mechanics via Mouse & Keyboard. Currently, this is supported purely with a dedicated or emulated gamepad.
- Some imagery rendering incorrectly, such as the manual. This should not affect the gameplay. 
- The current state of the output has not been thoroughly tested, though preliminary tests do suggest less conversion errors than the prior *OcculticKonosuba* project. Please report any unknown issues.

**Things that may be added eventually:**
- PS Vita and Xbox One support for *OCCULTIC;NINE*.
- Xbox One support for *STEINS;GATE 0*.
- Support for *DUNAMIS15* in some capacity.
- [Meta] Layout in this readme for keybinds.
