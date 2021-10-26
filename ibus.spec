%global with_pkg_config %(pkg-config --version >/dev/null 2>&1 && echo -n "1" || echo -n "0")
%global with_kde5 1
%global ibus_api_version 1.0
%global __python %{__python3}
%global dbus_python_version 0.83.0

Name:                   ibus
Version:                1.5.19
Release:                9
Summary:                Intelligent Input Bus for Linux OS
License:                LGPLv2+
URL:                    https://github.com/ibus/%name/wiki
Source0:                https://github.com/ibus/ibus/releases/download/%{version}/%{name}-%{version}.tar.gz
#Source1,2 come form fedora
Source1:                %{name}-xinput
Source2:                %{name}.conf.5
Source3:                https://fujiwara.fedorapeople.org/ibus/po/%{name}-po-1.5.19-20180822.tar.gz
Patch0:                 %{name}-HEAD.patch
Patch1:                 %{name}-1385349-segv-bus-proxy.patch
Patch6000:              backport-0001-CVE-2019-14822.patch
Patch6001:              backport-0002-CVE-2019-14822.patch

BuildRequires:          gettext-devel libtool glib2-doc gtk2-devel gtk3-devel dbus-glib-devel gtk-doc dconf-devel dbus-x11 python3-devel
BuildRequires:          dbus-python-devel >= %{dbus_python_version} desktop-file-utils python3-gobject python2-devel vala vala-devel vala-tools
BuildRequires:          GConf2-devel intltool iso-codes-devel libnotify-devel libwayland-client-devel qt5-qtbase-devel cldr-emoji-annotation
BuildRequires:          unicode-emoji unicode-ucd libXtst-devel libxslt gobject-introspection-devel pygobject3-devel

Requires:               iso-codes dbus-x11 dconf python3-gobject python3
Requires:               xorg-x11-xinit xorg-x11-xkb-utils

Requires:               desktop-file-utils glib2
Requires(post):         desktop-file-utils glib2 
Requires(postun):       desktop-file-utils
Requires:               dconf
Requires(postun):       dconf
Requires(posttrans):    dconf
Requires:               %{_sbindir}/alternatives
Requires(post):         %{_sbindir}/alternatives
Requires(postun):       %{_sbindir}/alternatives

Provides:               ibus-gtk = %{version}-%{release}
Obsoletes:              ibus-gtk < %{version}-%{release}
Provides:               ibus-gtk2  ibus-gtk3  ibus-setup  ibus-wayland
Obsoletes:              ibus-gtk2  ibus-gtk3  ibus-setup  ibus-wayland

%global _xinputconf %{_sysconfdir}/X11/xinit/xinput.d/ibus.conf

%description
IBus means Intelligent Input Bus. It is an input framework for Linux OS.

%package libs
Summary:        IBus libraries
Requires:       dbus >= 1.2.4
Requires:       glib2 gobject-introspection

%description libs
This package contains the libraries for IBus

%package devel
Summary:                Development tools for ibus
Requires:               %{name} = %{version}-%{release}
Requires:               dbus-devel glib2-devel gobject-introspection-devel vala
Provides:               ibus-devel-docs
Obsoletes:              ibus-devel-docs

%package_help

%description devel
The ibus-devel package contains the header files and developer
docs for ibus.

%prep
%autosetup -p1

zcat %SOURCE3 | tar xfv -

diff client/gtk2/ibusimcontext.c client/gtk3/ibusimcontext.c
if test $? -ne 0 ; then
    echo "Have to copy ibusimcontext.c into client/gtk3"
    abort
fi

%build
autoreconf -ivf
%configure --disable-static --enable-gtk2 --enable-gtk3 --enable-xim --enable-gtk-doc --enable-surrounding-text \
           --with-python=python3 --disable-python2 --enable-wayland --enable-introspection %{nil}

make -C ui/gtk3 maintainer-clean-generic
make

%install
%make_install INSTALL='install -p'
%delete_la

for S in %{SOURCE2}
do
  cp $S .
  MP=`basename $S` 
  gzip $MP
  install -pm 644 -D ${MP}.gz $RPM_BUILD_ROOT%{_datadir}/man/man5/${MP}.gz
done

install -pm 644 -D %{SOURCE1} $RPM_BUILD_ROOT%{_xinputconf}

echo "NoDisplay=true" >> $RPM_BUILD_ROOT%{_datadir}/applications/ibus-setup.desktop

desktop-file-install --delete-original          \
  --dir $RPM_BUILD_ROOT%{_datadir}/applications \
  $RPM_BUILD_ROOT%{_datadir}/applications/*

%find_lang %{name}10

%check
make check DISABLE_GUI_TESTS="ibus-compose ibus-keypress test-stress" VERBOSE=1 %{nil}

%post
%{_sbindir}/alternatives --install %{_sysconfdir}/X11/xinit/xinputrc xinputrc %{_xinputconf} 83 || :

%postun
if [ "$1" -eq 0 ]; then
  %{_sbindir}/alternatives --remove xinputrc %{_xinputconf} || :
  [ -L %{_sysconfdir}/alternatives/xinputrc -a "`readlink %{_sysconfdir}/alternatives/xinputrc`" = "%{_xinputconf}" ] && %{_sbindir}/alternatives --auto xinputrc || :

  dconf update || :
  [ -f %{_sysconfdir}/dconf/db/ibus ] && \
      rm %{_sysconfdir}/dconf/db/ibus || :
  [ -f /var/cache/ibus/bus/registry ] && \
      rm /var/cache/ibus/bus/registry || :
fi

%posttrans
dconf update || :
[ -x %{_bindir}/ibus ] && \
  %{_bindir}/ibus write-cache --system &>/dev/null || :

%ldconfig_scriptlets libs

%files -f %{name}10.lang
%defattr(-,root,root)
%doc COPYING AUTHORS COPYING.unicode
%{_bindir}/ibus
%{_bindir}/ibus-daemon
%{_bindir}/ibus-setup
%{_datadir}/applications/*.desktop
%{_datadir}/bash-completion/completions/ibus.bash
%{_datadir}/dbus-1/services/*.service
%{_datadir}/GConf/gsettings/*
%{_datadir}/glib-2.0/schemas/*.xml
%{_datadir}/ibus/*
%{_datadir}/icons/hicolor/*/apps/*
%{_libexecdir}/*
%{_sysconfdir}/dconf/db/ibus.d
%{_sysconfdir}/dconf/profile/ibus
%python3_sitearch/gi/overrides/__pycache__/*.py*
%python3_sitearch/gi/overrides/IBus.py
%dir %{_sysconfdir}/X11/xinit/xinput.d
%config %{_xinputconf}
%{_libdir}/gtk-2.0/*
%{_libdir}/gtk-3.0/*

%files libs
%{_libdir}/libibus-*%{ibus_api_version}.so.*
%{_libdir}/girepository-1.0/IBus*-1.0.typelib

%files devel
%defattr(-,root,root)
%{_libdir}/lib*.so
%{_libdir}/pkgconfig/*
%{_includedir}/*
%{_datadir}/gir-1.0/IBus*-1.0.gir
%{_datadir}/vala/vapi/ibus-*1.0.vapi
%{_datadir}/vala/vapi/ibus-*1.0.deps

%files help
%defattr(-,root,root)
%doc README
%{_datadir}/man/*/*
%{_datadir}/gtk-doc/html/*

%changelog
* Tue Oct 26 2021 wangkerong <wangkerong@huawei.com> - 1.5.19-9
- Type:CVE
- ID:CVE-2019-14822
- SUG:NA
- DESC:fix CVE-2019-14822

* Tue Sep 8 2020 hanhui <hanhui15@huawei.com> - 1.5.19-8
- Type:bugfix
- ID:NA
- SUG:NA
- DESC:modify source url

* Wed Feb 26 2020 hexiujun <hexiujun1@huawei.com> - 1.5.19-7
- Type:enhancement
- ID:NA
- SUG:NA
- DESC:deprecated python2

* Wed Oct 09 2019 openEuler Buildteam <buildteam@openeuler.org> - 1.5.19-6
- Type:enhancement
- ID:NA
- SUG:NA
- DESC:add COPYING.unicode 

* Thu Sep 19 2019 openEuler Buildteam <buildteam@openeuler.org> - 1.5.19-5
- Package init

