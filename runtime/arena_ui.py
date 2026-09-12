"""Native controls for the two physical sources. Call UI methods on AppKit's main thread."""
import objc
from AppKit import (
    NSObject, NSWindow, NSWindowStyleMaskTitled, NSWindowStyleMaskClosable,
    NSBackingStoreBuffered, NSTextField, NSButton, NSSlider, NSPopUpButton,
    NSButtonTypeSwitch, NSApplication, NSBeep,
)


class ArenaPanel(NSObject):
    @objc.python_method
    def build(self, controls, lock):
        self.controls, self.lock = controls, lock
        height = 680 if controls.get('cns_mode') else 580
        self.panel = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((0, 0), (340, height)), NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered, False)
        self.panel.setTitle_('Fly arena controls')
        self.panel.setReleasedWhenClosed_(False)
        view = self.panel.contentView()

        def label(text, y, height=22):
            item = NSTextField.labelWithString_(text)
            item.setFrame_(((18, y), (304, height)))
            view.addSubview_(item)
            return item

        def action(item, tag):
            item.setTag_(tag)
            item.setTarget_(self)
            item.setAction_('change:')
            view.addSubview_(item)
            return item

        def button(text, y, tag):
            item = NSButton.alloc().initWithFrame_(((18, y), (304, 28)))
            item.setTitle_(text)
            item.setBezelStyle_(1)
            return action(item, tag)

        if controls.get('cns_mode'):
            self.release_block = NSButton.alloc().initWithFrame_(((18, 647), (304, 24)))
            self.release_block.setButtonType_(NSButtonTypeSwitch)
            self.release_block.setTitle_('Block neuromuscular release (assay)')
            action(self.release_block, 13)
            button('Pause and save individual', 612, 11)
            button('Restore saved individual (paused)', 578, 12)

        self.selected = action(NSPopUpButton.alloc().initWithFrame_pullsDown_(((18, 540), (304, 28)), False), 0)
        self.selected.addItemsWithTitles_(['Source 1', 'Source 2'])
        self.enabled = NSButton.alloc().initWithFrame_(((18, 505), (304, 24)))
        self.enabled.setButtonType_(NSButtonTypeSwitch)
        self.enabled.setTitle_('Source enabled')
        action(self.enabled, 1)
        label('Position (mm):       x                         y', 474)
        self.x = action(NSTextField.alloc().initWithFrame_(((112, 450), (85, 24))), 2)
        self.y = action(NSTextField.alloc().initWithFrame_(((234, 450), (85, 24))), 3)
        self.odor_label = label('Food odor strength', 414)
        self.odor = action(NSSlider.alloc().initWithFrame_(((18, 390), (304, 24))), 4)
        self.odor.setMinValue_(0); self.odor.setMaxValue_(1)
        self.odor.setContinuous_(False)
        label('Taste on mouth contact', 356)
        self.taste = action(NSPopUpButton.alloc().initWithFrame_pullsDown_(((18, 327), (304, 28)), False), 5)
        self.taste.addItemsWithTitles_(['Neutral', 'Sweet', 'Bitter'])
        self.heat_label = label('Source temperature', 293)
        self.heat = action(NSSlider.alloc().initWithFrame_(((18, 269), (304, 24))), 6)
        self.heat.setMinValue_(22); self.heat.setMaxValue_(45)
        self.heat.setContinuous_(False)
        self.liquid = NSButton.alloc().initWithFrame_(((18, 236), (304, 24)))
        self.liquid.setButtonType_(NSButtonTypeSwitch)
        self.liquid.setTitle_('Liquid surface')
        action(self.liquid, 10)
        button('Place at camera target', 198, 7)
        button('Place at mouth (contact experiment)', 164, 8)
        button('Free camera', 130, 9)
        label('Sensory-only experiment.\nDirect walking stimulation is disabled.', 89, 37)
        label('Pain pathway: not mapped.\n' + ('Heating and cooling inputs enabled.' if controls.get('cns_mode')
              else 'Temperature drives warmth receptors only.'), 48, 40)
        self.status = label('Sensory inputs only. No navigation policy.', 9, 35)
        self.refresh()
        app = NSApplication.sharedApplication()
        window = app.keyWindow()
        if window is not None:
            frame, screen = window.frame(), window.screen().visibleFrame()
            x = min(frame.origin.x + frame.size.width + 12,
                    screen.origin.x + screen.size.width - 345)
            self.panel.setFrameOrigin_((max(screen.origin.x, x),
                max(screen.origin.y, frame.origin.y + frame.size.height - height)))
        else:
            self.panel.center()
        self.panel.makeKeyAndOrderFront_(None)
        return self

    @objc.python_method
    def refresh(self):
        with self.lock:
            selected = self.controls['selected_source']
            source = dict(self.controls['sources'][selected])
            release_block = self.controls.get('release_block', False)
        self.selected.selectItemAtIndex_(selected)
        self.enabled.setState_(int(source['enabled']))
        self.x.setStringValue_(f'{source["x"]:.2f}')
        self.y.setStringValue_(f'{source["y"]:.2f}')
        self.odor.setDoubleValue_(source['odor'])
        self.odor_label.setStringValue_(f'Food odor strength: {source["odor"]:.2f}')
        self.taste.selectItemAtIndex_(['neutral', 'sweet', 'bitter'].index(source['taste']))
        self.heat.setDoubleValue_(source['temperature'])
        self.heat_label.setStringValue_(f'Source temperature: {source["temperature"]:.1f} °C')
        self.liquid.setState_(int(source.get('liquid', True)))
        if self.controls.get('cns_mode'):
            self.release_block.setState_(int(release_block))

    @objc.IBAction
    def change_(self, sender):
        try:
            with self.lock:
                source = self.controls['sources'][self.controls['selected_source']]
                tag = sender.tag()
                if tag == 0:
                    self.controls['selected_source'] = sender.indexOfSelectedItem()
                elif tag == 1:
                    source['enabled'] = bool(sender.state())
                elif tag in (2, 3):
                    value = float(sender.stringValue())
                    if not -100 <= value <= 100:
                        raise ValueError('Position must be within ±100 mm')
                    source['x' if tag == 2 else 'y'] = value
                elif tag == 4:
                    source['odor'] = sender.doubleValue()
                elif tag == 5:
                    source['taste'] = ['neutral', 'sweet', 'bitter'][sender.indexOfSelectedItem()]
                elif tag == 6:
                    source['temperature'] = sender.doubleValue()
                elif tag in (7, 8):
                    self.controls['place_source'] = 'camera' if tag == 7 else 'mouth'
                elif tag == 9:
                    self.controls['camera'] = 2
                elif tag == 10:
                    source['liquid'] = bool(sender.state())
                elif tag in (11, 12) and self.controls.get('cns_mode'):
                    self.controls['checkpoint_action'] = 'save' if tag == 11 else 'restore'
                    self.controls['paused'] = True
                elif tag == 13 and self.controls.get('cns_mode'):
                    self.controls['release_block'] = bool(sender.state())
        except (ValueError, TypeError):
            NSBeep()
        self.refresh()
