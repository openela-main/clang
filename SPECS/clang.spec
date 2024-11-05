%bcond_with snapshot_build

%if %{with snapshot_build}
%{llvm_sb}
%endif

# Opt out of https://fedoraproject.org/wiki/Changes/fno-omit-frame-pointer
# https://bugzilla.redhat.com/show_bug.cgi?id=2158587
%undefine _include_frame_pointers

%bcond_with compat_build
%bcond_without check

%ifarch aarch64
# Use lld on aarch64, becuase ld.bfd will occasionally fail with the error:
# `Could not create temporary file: Too many open files`
%bcond_without linker_lld
%if 0%{?rhel} == 8
# RHEL8 does not pass --build-id to the linker by default, so we need
# to manually specify the build-id algorith that rpmbuild expects.
# lld defaults to a different algorithm.
%global build_ldflags %(echo %{build_ldflags} -Wl,--build-id=sha1)
%endif
%else
%bcond_with linker_lld
%endif

%global maj_ver 18
%global min_ver 1
%global patch_ver 8
#global rc_ver 4

%if %{with snapshot_build}
%undefine rc_ver
%global maj_ver %{llvm_snapshot_version_major}
%global min_ver %{llvm_snapshot_version_minor}
%global patch_ver %{llvm_snapshot_version_patch}
%endif

%global clang_version %{maj_ver}.%{min_ver}.%{patch_ver}

%if %{with compat_build}
%global pkg_name clang%{maj_ver}
# Install clang to same prefix as llvm, so that apps that use llvm-config
# will also be able to find clang libs.
%global install_prefix %{_libdir}/llvm%{maj_ver}
%global install_bindir %{install_prefix}/bin
%global install_includedir %{install_prefix}/include
%global install_libdir %{install_prefix}/lib
%global install_datadir %{install_prefix}/share
%global install_libexecdir %{install_prefix}/libexec
%global install_docdir %{install_datadir}/doc

%global pkg_includedir %{install_includedir}
%else
%global pkg_name clang
%global install_prefix %{_prefix}
%global install_bindir %{_bindir}
%global install_datadir %{_datadir}
%global install_libdir %{_libdir}
%global install_includedir %{_includedir}
%global install_libexecdir %{_libexecdir}
%global install_docdir %{_docdir}
%endif

%ifarch ppc64le aarch64
# Too many threads on some systems causes OOM errors.
%global _smp_mflags -j8
%endif

# Try to limit memory use on i686.
%if !0%{?rhel} > 8
%ifarch %ix86
%constrain_build -m 3072
%endif
%endif

%global clang_srcdir clang-%{clang_version}%{?rc_ver:rc%{rc_ver}}.src
%global clang_tools_srcdir clang-tools-extra-%{clang_version}%{?rc_ver:rc%{rc_ver}}.src

Name:		%pkg_name
Version:	%{clang_version}%{?rc_ver:~rc%{rc_ver}}%{?llvm_snapshot_version_suffix:~%{llvm_snapshot_version_suffix}}
Release:	1%{?dist}
Summary:	A C language family front-end for LLVM

License:	NCSA
URL:		http://llvm.org
%if %{with snapshot_build}
Source0:    %{llvm_snapshot_source_prefix}clang-%{llvm_snapshot_yyyymmdd}.src.tar.xz
Source1:    %{llvm_snapshot_source_prefix}clang-tools-extra-%{llvm_snapshot_yyyymmdd}.src.tar.xz
%{llvm_snapshot_extra_source_tags}

%else
Source0:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{clang_version}%{?rc_ver:-rc%{rc_ver}}/%{clang_srcdir}.tar.xz
Source3:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{clang_version}%{?rc_ver:-rc%{rc_ver}}/%{clang_srcdir}.tar.xz.sig
Source1:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{clang_version}%{?rc_ver:-rc%{rc_ver}}/%{clang_tools_srcdir}.tar.xz
Source2:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{clang_version}%{?rc_ver:-rc%{rc_ver}}/%{clang_tools_srcdir}.tar.xz.sig
Source4:	release-keys.asc
%endif
%if %{without compat_build}
Source5:	macros.%{name}
%endif
# This file is still needed because We still build on F38 in the
# upstream-snapshot branch.
Source6:	clang.cfg

# Patches for clang
Patch1:     0001-PATCH-clang-Make-funwind-tables-the-default-on-all-a.patch
Patch2:     0003-PATCH-clang-Don-t-install-static-libraries.patch
# Workaround a bug in ORC on ppc64le.
# More info is available here: https://reviews.llvm.org/D159115#4641826
Patch5:     0001-Workaround-a-bug-in-ORC-on-ppc64le.patch

# RHEL specific patches
# Avoid unwanted dependency on python-myst-parser
Patch101:  0009-disable-myst-parser.patch

# Patches for clang-tools-extra
# See https://reviews.llvm.org/D120301
Patch201:   0001-clang-tools-extra-Make-test-dependency-on-LLVMHello-.patch

BuildRequires:	gcc
BuildRequires:	gcc-c++
BuildRequires:	clang
%if %{with linker_lld}
BuildRequires:	lld
%endif
BuildRequires:	cmake
BuildRequires:	ninja-build

%if %{with compat_build}
%global llvm_pkg_name llvm%{maj_ver}
%else
%global llvm_pkg_name llvm
BuildRequires:  %{llvm_pkg_name}-test = %{version}
BuildRequires:  %{llvm_pkg_name}-googletest = %{version}
%endif

BuildRequires:	%{llvm_pkg_name}-devel = %{version}
# llvm-static is required, because clang-tablegen needs libLLVMTableGen, which
# is not included in libLLVM.so.
BuildRequires:	%{llvm_pkg_name}-static = %{version}
BuildRequires:	%{llvm_pkg_name}-cmake-utils = %{version}

BuildRequires:	libxml2-devel
BuildRequires:	perl-generators
BuildRequires:	ncurses-devel
# According to https://fedoraproject.org/wiki/Packaging:Emacs a package
# should BuildRequires: emacs if it packages emacs integration files.
BuildRequires:	emacs

# The testsuite uses /usr/bin/lit which is part of the python3-lit package.
BuildRequires:	python3-lit

BuildRequires:	python3-sphinx
BuildRequires:	pandoc
%if %{undefined rhel}
BuildRequires:	python3-myst-parser
%endif
BuildRequires:	libatomic

# We need python3-devel for %%py3_shebang_fix
BuildRequires:	python3-devel

%if ! 0%{?rhel}
# For reproducible pyc file generation
# See https://docs.fedoraproject.org/en-US/packaging-guidelines/Python_Appendix/#_byte_compilation_reproducibility
BuildRequires: /usr/bin/marshalparser
%if %{without compat_build}
%global py_reproducible_pyc_path %{buildroot}%{python3_sitelib}
%endif
%endif

# Needed for %%multilib_fix_c_header
BuildRequires:	multilib-rpm-config

# For origin certification
BuildRequires:	gnupg2

# scan-build uses these perl modules so they need to be installed in order
# to run the tests.
BuildRequires: perl(Digest::MD5)
BuildRequires: perl(File::Copy)
BuildRequires: perl(File::Find)
BuildRequires: perl(File::Path)
BuildRequires: perl(File::Temp)
BuildRequires: perl(FindBin)
BuildRequires: perl(Hash::Util)
BuildRequires: perl(lib)
BuildRequires: perl(Term::ANSIColor)
BuildRequires: perl(Text::ParseWords)
BuildRequires: perl(Sys::Hostname)

Requires:	%{name}-libs%{?_isa} = %{version}-%{release}

# clang requires gcc, clang++ requires libstdc++-devel
# - https://bugzilla.redhat.com/show_bug.cgi?id=1021645
# - https://bugzilla.redhat.com/show_bug.cgi?id=1158594
Requires:	libstdc++-devel
Requires:	gcc-c++

Provides:	clang(major) = %{maj_ver}

Conflicts:	compiler-rt < 11.0.0

%description
clang: noun
    1. A loud, resonant, metallic sound.
    2. The strident call of a crane or goose.
    3. C-language family front-end toolkit.

The goal of the Clang project is to create a new C, C++, Objective C
and Objective C++ front-end for the LLVM compiler. Its tools are built
as libraries and designed to be loosely-coupled and extensible.

Install compiler-rt if you want the Blocks C language extension or to
enable sanitization and profiling options when building, and
libomp-devel to enable -fopenmp.

%package libs
Summary: Runtime library for clang
Requires: %{name}-resource-filesystem = %{version}
# RHEL specific: Use libstdc++ from gcc13 by default. rhbz#2178804
Requires: gcc-toolset-13-gcc-c++
Recommends: compiler-rt%{?_isa} = %{version}
# libomp-devel is required, so clang can find the omp.h header when compiling
# with -fopenmp.
Recommends: libomp-devel%{_isa} = %{version}
Recommends: libomp%{_isa} = %{version}

%description libs
Runtime library for clang.

%package devel
Summary: Development header files for clang
Requires: %{name}-libs = %{version}-%{release}
Requires: %{name}%{?_isa} = %{version}-%{release}
# The clang CMake files reference tools from clang-tools-extra.
Requires: %{name}-tools-extra%{?_isa} = %{version}-%{release}
Provides: clang-devel(major) = %{maj_ver}

%description devel
Development header files for clang.

%package resource-filesystem
Summary: Filesystem package that owns the clang resource directory
Provides: clang-resource-filesystem(major) = %{maj_ver}
BuildArch: noarch

%description resource-filesystem
This package owns the clang resouce directory: lib/clang/$version/

%package analyzer
Summary:	A source code analysis framework
License:	NCSA and MIT
BuildArch:	noarch
Requires:	%{name} = %{version}-%{release}

%description analyzer
The Clang Static Analyzer consists of both a source code analysis
framework and a standalone tool that finds bugs in C and Objective-C
programs. The standalone tool is invoked from the command-line, and is
intended to run in tandem with a build of a project or code base.

%package tools-extra
Summary:	Extra tools for clang
Requires:	%{name}-libs%{?_isa} = %{version}-%{release}
Requires:	emacs-filesystem

%description tools-extra
A set of extra tools built using Clang's tooling API.

%package tools-extra-devel
Summary: Development header files for clang tools
Requires: %{name}-tools-extra = %{version}-%{release}

%description tools-extra-devel
Development header files for clang tools.

# Put git-clang-format in its own package, because it Requires git
# and we don't want to force users to install all those dependenices if they
# just want clang.
%package -n git-clang-format
Summary:	Integration of clang-format for git
Requires:	%{name}-tools-extra = %{version}-%{release}
Requires:	git
Requires:	python3

%description -n git-clang-format
clang-format integration for git.

%if %{without compat_build}
%package -n python3-clang
Summary:       Python3 bindings for clang
Requires:      %{name}-devel%{?_isa} = %{version}-%{release}
Requires:      python3
%description -n python3-clang
%{summary}.


%prep
%if %{without snapshot_build}
%{gpgverify} --keyring='%{SOURCE4}' --signature='%{SOURCE3}' --data='%{SOURCE0}'
%endif


%if %{without snapshot_build}
%{gpgverify} --keyring='%{SOURCE4}' --signature='%{SOURCE2}' --data='%{SOURCE1}'
%endif

%setup -T -q -b 1 -n %{clang_tools_srcdir}
%autopatch -m200 -p2

# failing test case
rm test/clang-tidy/checkers/altera/struct-pack-align.cpp

%py3_shebang_fix \
	clang-tidy/tool/ \
	clang-include-fixer/find-all-symbols/tool/run-find-all-symbols.py


%setup -q -n %{clang_srcdir}
%autopatch -M%{?!rhel:100}%{?rhel:200} -p2

# failing test case
rm test/CodeGen/profile-filter.c

%py3_shebang_fix \
	tools/clang-format/ \
	tools/clang-format/git-clang-format \
	utils/hmaptool/hmaptool \
	tools/scan-view/bin/scan-view \
	tools/scan-view/share/Reporter.py \
	tools/scan-view/share/startfile.py \
	tools/scan-build-py/bin/* \
	tools/scan-build-py/libexec/*

# Convert markdown files to rst to cope with the absence of compatible md parser in rhel.
# The sed expression takes care of a slight difference between pandoc markdown and sphinx markdown.
find -name '*.md' | while read md; do sed -r -e 's/^( )*\* /\n\1\* /' ${md} | pandoc -f markdown -o ${md%.md}.rst  ; done

%endif

%build

%undefine __cmake_in_source_build

# Disable lto on i686 due to memory constraints.
%ifarch %ix86
%define _lto_cflags %{nil}
%endif

# Disable LTO to speed up builds
%if %{with snapshot_build}
%global _lto_cflags %nil
%endif

%ifarch s390 s390x aarch64 %ix86 ppc64le
# Decrease debuginfo verbosity to reduce memory consumption during final library linking
%global optflags %(echo %{optflags} | sed 's/-g /-g1 /')
%endif

%if %{with linker_lld}
# TODO: Use LLVM_USE_LLD cmake option, but this doesn't seem to work with
# standalone builds.
%global build_ldflags %(echo %{build_ldflags} -fuse-ld=lld)
%endif

# Disable dwz on aarch64, because it takes a huge amount of time to decide not to optimize things.
%ifarch aarch64
%define _find_debuginfo_dwz_opts %{nil}
%endif


%set_build_flags
CXXFLAGS="$CXXFLAGS -Wno-address -Wno-nonnull -Wno-maybe-uninitialized"
CFLAGS="$CFLAGS -Wno-address -Wno-nonnull -Wno-maybe-uninitialized"

# We set CLANG_DEFAULT_PIE_ON_LINUX=OFF and PPC_LINUX_DEFAULT_IEEELONGDOUBLE=ON to match the
# defaults used by Fedora's GCC.
%cmake -G Ninja \
	-DCLANG_DEFAULT_PIE_ON_LINUX=OFF \
%if 0%{?fedora} || 0%{?rhel} > 9
	-DPPC_LINUX_DEFAULT_IEEELONGDOUBLE=ON \
%endif
	-DLLVM_PARALLEL_LINK_JOBS=1 \
	-DLLVM_LINK_LLVM_DYLIB:BOOL=ON \
	-DCMAKE_BUILD_TYPE=RelWithDebInfo \
	-DPYTHON_EXECUTABLE=%{__python3} \
	-DCMAKE_SKIP_RPATH:BOOL=ON \
%ifarch s390 s390x %ix86 ppc64le aarch64
	-DCMAKE_C_FLAGS_RELWITHDEBINFO="%{optflags} -DNDEBUG" \
	-DCMAKE_CXX_FLAGS_RELWITHDEBINFO="%{optflags} -DNDEBUG" \
%endif
%if %{with compat_build}
	-DCMAKE_INSTALL_PREFIX=%{install_prefix} \
	-DLLVM_CMAKE_DIR=%{install_libdir}/cmake/llvm \
%else
%if 0%{?__isa_bits} == 64
	-DLLVM_LIBDIR_SUFFIX=64 \
%else
	-DLLVM_LIBDIR_SUFFIX= \
%endif
%endif
	-DCLANG_INCLUDE_TESTS:BOOL=ON \
	-DLLVM_BUILD_UTILS:BOOL=ON \
	-DLLVM_EXTERNAL_CLANG_TOOLS_EXTRA_SOURCE_DIR=../%{clang_tools_srcdir} \
	-DLLVM_EXTERNAL_LIT=%{_bindir}/lit \
	-DLLVM_LIT_ARGS="-vv" \
	-DLLVM_MAIN_SRC_DIR=%{_datadir}/llvm/src \
	\
%if %{with snapshot_build}
	-DLLVM_VERSION_SUFFIX="%{llvm_snapshot_version_suffix}" \
%endif
	\
%if %{with compat_build}
	-DLLVM_TABLEGEN_EXE:FILEPATH=%{_bindir}/llvm-tblgen-%{maj_ver} \
%else
	-DLLVM_TABLEGEN_EXE:FILEPATH=%{_bindir}/llvm-tblgen \
%endif
	-DLLVM_COMMON_CMAKE_UTILS=%{install_datadir}/llvm/cmake \
	-DCLANG_ENABLE_ARCMT:BOOL=ON \
	-DCLANG_ENABLE_STATIC_ANALYZER:BOOL=ON \
	-DCLANG_INCLUDE_DOCS:BOOL=ON \
	-DCLANG_PLUGIN_SUPPORT:BOOL=ON \
	-DENABLE_LINKER_BUILD_ID:BOOL=ON \
	-DLLVM_ENABLE_EH=ON \
	-DLLVM_ENABLE_RTTI=ON \
	-DLLVM_BUILD_DOCS=ON \
	-DLLVM_RAM_PER_COMPILE_JOB=3000 \
	-DLLVM_ENABLE_SPHINX=ON \
	-DCLANG_LINK_CLANG_DYLIB=ON \
	-DSPHINX_WARNINGS_AS_ERRORS=OFF \
	\
	-DCLANG_BUILD_EXAMPLES:BOOL=OFF \
	-DBUILD_SHARED_LIBS=OFF \
	-DCLANG_REPOSITORY_STRING="%{?fedora:Fedora}%{?rhel:Red Hat} %{version}-%{release}" \
	-DGCC_INSTALL_PREFIX=/opt/rh/gcc-toolset-13/root/usr \
	-DCLANG_RESOURCE_DIR=../lib/clang/%{maj_ver} \
	-DCLANG_CONFIG_FILE_SYSTEM_DIR=%{_sysconfdir}/%{name}/ \
%ifarch %{arm}
	-DCLANG_DEFAULT_LINKER=lld \
%endif
	-DCLANG_DEFAULT_UNWINDLIB=libgcc

%cmake_build

%ifarch aarch64
# Strip .gnu.build.attrib sections, because find-debuginfo.sh is failing to strip debug info,
# because there are too many of them.
# https://issues.redhat.com/browse/RHEL-43211
for f in lib64/libclang-cpp.so.%{maj_ver}.%{min_ver} lib64/libclang.so.%{maj_ver}.%{min_ver}.%{patch_ver} bin/c-index-test bin/clang-tidy bin/clangd; do
  objcopy  -R '.gnu.build.attrib*' aarch64-redhat-linux-gnu/$f
done
%endif


%install

%cmake_install

# Add a symlink in /usr/bin to clang-format-diff
ln -s %{install_datadir}/clang/clang-format-diff.py %{buildroot}%{install_bindir}/clang-format-diff

# File in the macros file for other packages to use.  We are not doing this
# in the compat package, because the version macros would # conflict with
# eachother if both clang and the clang compat package were installed together.
%if %{without compat_build}
install -p -m0644 -D %{SOURCE5} %{buildroot}%{_rpmmacrodir}/macros.%{name}
sed -i -e "s|@@CLANG_MAJOR_VERSION@@|%{maj_ver}|" \
       -e "s|@@CLANG_MINOR_VERSION@@|%{min_ver}|" \
       -e "s|@@CLANG_PATCH_VERSION@@|%{patch_ver}|" \
       %{buildroot}%{_rpmmacrodir}/macros.%{name}

# install clang python bindings
mkdir -p %{buildroot}%{python3_sitelib}/clang/
install -p -m644 bindings/python/clang/* %{buildroot}%{python3_sitelib}/clang/
%py_byte_compile %{__python3} %{buildroot}%{python3_sitelib}/clang

# install scanbuild-py to python sitelib.
mv %{buildroot}%{_prefix}/%{_lib}/{libear,libscanbuild} %{buildroot}%{python3_sitelib}
%py_byte_compile %{__python3} %{buildroot}%{python3_sitelib}/{libear,libscanbuild}

# Move emacs integration files to the correct directory
mkdir -p %{buildroot}%{_emacs_sitestartdir}
for f in clang-format.el clang-rename.el clang-include-fixer.el; do
mv %{buildroot}{%{_datadir}/clang,%{_emacs_sitestartdir}}/$f
done

# Create Manpage symlinks
ln -s clang.1.gz %{buildroot}%{_mandir}/man1/clang++.1.gz
ln -s clang.1.gz %{buildroot}%{_mandir}/man1/clang-%{maj_ver}.1.gz
ln -s clang.1.gz %{buildroot}%{_mandir}/man1/clang++-%{maj_ver}.1.gz

# Fix permission
chmod u-x %{buildroot}%{_mandir}/man1/scan-build.1*

# Add clang++-{version} symlink
ln -s clang++ %{buildroot}%{_bindir}/clang++-%{maj_ver}

%else
# Not sure where to put these python modules for the compat build.
rm -Rf %{buildroot}%{install_libdir}/{libear,libscanbuild}

# Not sure where to put the emacs integration files for the compat build.
rm -Rf %{buildroot}%{install_datadir}/clang/*.el

# Not sure what to do with man pages for the compat builds
rm -Rf %{buildroot}%{install_prefix}/share/man/

# Add version suffix to binaries
mkdir -p %{buildroot}%{_bindir}
for f in %{buildroot}/%{install_bindir}/*; do
  filename=`basename $f`
  if echo $filename | grep -e '%{maj_ver}'; then
    continue
  fi
  ln -s ../../%{install_bindir}/$filename %{buildroot}/%{_bindir}/$filename-%{maj_ver}
done

# Add clang++-{version} symlink
ln -s ../../%{install_bindir}/clang++  %{buildroot}%{install_bindir}/clang++-%{maj_ver}

%endif

%if 0%{?fedora} == 38 || 0%{?rhel} <= 8
# Install config file
mkdir -p %{buildroot}%{_sysconfdir}/%{name}/
mv %{SOURCE6} %{buildroot}%{_sysconfdir}/%{name}/%{_target_platform}.cfg
%endif

# Install config file for clang
%if %{maj_ver} >=18
mkdir -p %{buildroot}%{_sysconfdir}/%{name}/
echo "--gcc-triple=%{_target_cpu}-redhat-linux" >> %{buildroot}%{_sysconfdir}/%{name}/%{_target_platform}.cfg
%endif

# Fix permissions of scan-view scripts
chmod a+x %{buildroot}%{install_datadir}/scan-view/{Reporter.py,startfile.py}

# multilib fix
%multilib_fix_c_header --file %{install_includedir}/clang/Config/config.h

# remove editor integrations (bbedit, sublime, emacs, vim)
rm -vf %{buildroot}%{install_datadir}/clang/clang-format-bbedit.applescript
rm -vf %{buildroot}%{install_datadir}/clang/clang-format-sublime.py*

# TODO: Package html docs
rm -Rvf %{buildroot}%{install_docdir}/Clang/clang/html
rm -Rvf %{buildroot}%{install_datadir}/clang/clang-doc-default-stylesheet.css
rm -Rvf %{buildroot}%{install_datadir}/clang/index.js

# TODO: What are the Fedora guidelines for packaging bash autocomplete files?
rm -vf %{buildroot}%{install_datadir}/clang/bash-autocomplete.sh


# Create sub-directories in the clang resource directory that will be
# populated by other packages
mkdir -p %{buildroot}%{install_prefix}/lib/clang/%{maj_ver}/{bin,include,lib,share}/

#Add versioned resource directory macro
mkdir -p %{buildroot}%{_rpmmacrodir}/
echo "%%clang%{maj_ver}_resource_dir %%{_prefix}/lib/clang/%{maj_ver}" >> %{buildroot}%{_rpmmacrodir}/macros.%{name}

%check
%if %{with check}
# Build test dependencies separately, to prevent invocations of host clang from being affected
# by LD_LIBRARY_PATH below.
%cmake_build --target clang-test-depends \
    ExtraToolsUnitTests ClangdUnitTests ClangIncludeCleanerUnitTests ClangPseudoUnitTests
# requires lit.py from LLVM utilities
# Set SOURCE_DATE_EPOCH to disable hardware acceleration on s390x
# See https://bugzilla.redhat.com/show_bug.cgi?id=1994082
SOURCE_DATE_EPOCH=1629181597 LD_LIBRARY_PATH=%{buildroot}/%{install_libdir} %{__ninja} %{_smp_mflags} check-all -C %{_vpath_builddir}
%endif


%files
%license LICENSE.TXT
%{install_bindir}/clang
%{install_bindir}/clang++
%{install_bindir}/clang-%{maj_ver}
%{install_bindir}/clang++-%{maj_ver}
%{install_bindir}/clang-cl
%{install_bindir}/clang-cpp
%if %{without compat_build}
%{_mandir}/man1/clang.1.gz
%{_mandir}/man1/clang++.1.gz
%{_mandir}/man1/clang-%{maj_ver}.1.gz
%{_mandir}/man1/clang++-%{maj_ver}.1.gz
%else
%{_bindir}/clang-%{maj_ver}
%{_bindir}/clang++-%{maj_ver}
%{_bindir}/clang-cl-%{maj_ver}
%{_bindir}/clang-cpp-%{maj_ver}
%endif

%files libs
%{install_prefix}/lib/clang/%{maj_ver}/include/*
%{install_libdir}/*.so.*
%{_sysconfdir}/%{name}/%{_target_platform}.cfg

%files devel
%{install_libdir}/*.so
%{install_includedir}/clang/
%{install_includedir}/clang-c/
%{install_libdir}/cmake/*
%{install_bindir}/clang-tblgen
%if %{with compat_build}
%{_bindir}/clang-tblgen-%{maj_ver}
%endif
%dir %{install_datadir}/clang/

%files resource-filesystem
%dir %{install_prefix}/lib/clang/
%dir %{install_prefix}/lib/clang/%{maj_ver}/
%dir %{install_prefix}/lib/clang/%{maj_ver}/bin/
%dir %{install_prefix}/lib/clang/%{maj_ver}/include/
%dir %{install_prefix}/lib/clang/%{maj_ver}/lib/
%dir %{install_prefix}/lib/clang/%{maj_ver}/share/
%{_rpmmacrodir}/macros.%{name}


%files analyzer
%{install_bindir}/scan-view
%{install_bindir}/scan-build
%{install_bindir}/analyze-build
%{install_bindir}/intercept-build
%{install_bindir}/scan-build-py
%if %{with compat_build}
%{_bindir}/scan-view-%{maj_ver}
%{_bindir}/scan-build-%{maj_ver}
%{_bindir}/analyze-build-%{maj_ver}
%{_bindir}/intercept-build-%{maj_ver}
%{_bindir}/scan-build-py-%{maj_ver}
%endif
%{install_libexecdir}/ccc-analyzer
%{install_libexecdir}/c++-analyzer
%{install_libexecdir}/analyze-c++
%{install_libexecdir}/analyze-cc
%{install_libexecdir}/intercept-c++
%{install_libexecdir}/intercept-cc
%{install_datadir}/scan-view/
%{install_datadir}/scan-build/
%if %{without compat_build}
%{_mandir}/man1/scan-build.1.*
%{python3_sitelib}/libear
%{python3_sitelib}/libscanbuild
%endif


%files tools-extra
%{install_bindir}/amdgpu-arch
%{install_bindir}/clang-apply-replacements
%{install_bindir}/clang-change-namespace
%{install_bindir}/clang-check
%{install_bindir}/clang-doc
%{install_bindir}/clang-extdef-mapping
%{install_bindir}/clang-format
%{install_bindir}/clang-include-cleaner
%{install_bindir}/clang-include-fixer
%{install_bindir}/clang-move
%{install_bindir}/clang-offload-bundler
%{install_bindir}/clang-offload-packager
%{install_bindir}/clang-linker-wrapper
%{install_bindir}/clang-pseudo
%{install_bindir}/clang-query
%{install_bindir}/clang-refactor
%{install_bindir}/clang-rename
%{install_bindir}/clang-reorder-fields
%{install_bindir}/clang-repl
%{install_bindir}/clang-scan-deps
%{install_bindir}/clang-tidy
%{install_bindir}/clangd
%{install_bindir}/diagtool
%{install_bindir}/hmaptool
%{install_bindir}/nvptx-arch
%{install_bindir}/pp-trace
%{install_bindir}/c-index-test
%{install_bindir}/find-all-symbols
%{install_bindir}/modularize
%{install_bindir}/clang-format-diff
%{install_bindir}/run-clang-tidy
%if %{with compat_build}
%{_bindir}/amdgpu-arch-%{maj_ver}
%{_bindir}/clang-apply-replacements-%{maj_ver}
%{_bindir}/clang-change-namespace-%{maj_ver}
%{_bindir}/clang-check-%{maj_ver}
%{_bindir}/clang-doc-%{maj_ver}
%{_bindir}/clang-extdef-mapping-%{maj_ver}
%{_bindir}/clang-format-%{maj_ver}
%{_bindir}/clang-include-cleaner-%{maj_ver}
%{_bindir}/clang-include-fixer-%{maj_ver}
%{_bindir}/clang-move-%{maj_ver}
%{_bindir}/clang-offload-bundler-%{maj_ver}
%{_bindir}/clang-offload-packager-%{maj_ver}
%{_bindir}/clang-linker-wrapper-%{maj_ver}
%{_bindir}/clang-pseudo-%{maj_ver}
%{_bindir}/clang-query-%{maj_ver}
%{_bindir}/clang-refactor-%{maj_ver}
%{_bindir}/clang-rename-%{maj_ver}
%{_bindir}/clang-reorder-fields-%{maj_ver}
%{_bindir}/clang-repl-%{maj_ver}
%{_bindir}/clang-scan-deps-%{maj_ver}
%{_bindir}/clang-tidy-%{maj_ver}
%{_bindir}/clangd-%{maj_ver}
%{_bindir}/diagtool-%{maj_ver}
%{_bindir}/hmaptool-%{maj_ver}
%{_bindir}/nvptx-arch-%{maj_ver}
%{_bindir}/pp-trace-%{maj_ver}
%{_bindir}/c-index-test-%{maj_ver}
%{_bindir}/find-all-symbols-%{maj_ver}
%{_bindir}/modularize-%{maj_ver}
%{_bindir}/clang-format-diff-%{maj_ver}
%{_bindir}/run-clang-tidy-%{maj_ver}
%else
%{_mandir}/man1/diagtool.1.gz
%{_emacs_sitestartdir}/clang-format.el
%{_emacs_sitestartdir}/clang-rename.el
%{_emacs_sitestartdir}/clang-include-fixer.el
%endif
%{install_datadir}/clang/clang-format.py*
%{install_datadir}/clang/clang-format-diff.py*
%{install_datadir}/clang/clang-include-fixer.py*
%{install_datadir}/clang/clang-tidy-diff.py*
%{install_datadir}/clang/run-find-all-symbols.py*
%{install_datadir}/clang/clang-rename.py*

%files tools-extra-devel
%{install_includedir}/clang-tidy/

%files -n git-clang-format
%{install_bindir}/git-clang-format
%if %{with compat_build}
%{_bindir}/git-clang-format-%{maj_ver}
%endif

%if %{without compat_build}
%files -n python3-clang
%{python3_sitelib}/clang/


%endif
%changelog
* Tue Jul 09 2024 Tom Stellard <tstellar@redhat.com> - 18.1.8-1
- 18.1.8 Release

* Thu Jun 27 2024 Tom Stellard <tstellar@redhat.com> - 18.1.2-7
- Strip .gnu.build-attrib* sections from some binaries too

* Sat Jun 22 2024 Tom Stellard <tstellar@redhat.com> - 18.1.2-6
- Strip .gnu.build-attrib* sections out of libraries

* Sat May 25 2024 Tom Stellard <tstellar@redhat.com> - 18.1.2-5
- Set SOURCE_DATE_EPOCH when testing

* Fri May 24 2024 Tom Stellard <tstellar@redhat.com> - 18.1.2-4
- Limit number of compile jobs to avoid running out of memory

* Thu Mar 21 2024 Tom Stellrd <tstellar@redhat.com> - 18.1.2-1
- 18.1.2 Release

* Wed Nov 29 2023 Nikita Popov <npopov@redhat.com> - 17.0.6-1
- Update to LLVM 17.0.6

* Wed Oct 04 2023 Nikita Popov <npopov@redhat.com> - 17.0.2-1
- Update to LLVM 17.0.2

* Thu Jun 29 2023 Tom Stellard <tstellar@redhat.com> - 16.0.6-2
- Use gcc-toolset-13 by default

* Sat Jun 17 2023 Tom Stellard <tstellar@redhat.com> - 16.0.6-1
- 16.0.6 Release

* Fri May 12 2023 Tom Stellard <tstellar@redhat.com> - 16.0.0-2
- Fix clang_resource_dir macro

* Fri Apr 28 2023 Tom Stellard <tstelar@redhat.com> - 16.0.0-1
- 16.0.0 Release

* Thu Jan 19 2023 Tom Stellard <tstellar@redhat.com> - 15.0.7-1
- Update to LLVM 15.0.7

* Tue Sep 06 2022 Nikita Popov <npopov@redhat.com> - 15.0.0-1
- Update to LLVM 15.0.0

* Tue Jun 28 2022 Tom Stellard <tstellar@redhat.com> - 14.0.6-1
- 14.0.6 Release

* Wed Jun 01 2022 Timm Bäder <tbaeder@redhat.com> - 14.0.0-2
- Increate gcc-toolset dependency to 12
- Set GCC_INSTALL_PREFIX variable

* Thu Apr 07 2022 Timm Bäder <tbaeder@redhat.com> - 14.0.0-1
- Update to 14.0.0

* Thu Feb 03 2022 Tom Stellard <tstellar@redhat.com> - 13.0.1-1
- 13.0.1 Release

* Fri Jan 21 2022 Serge Guelton - 13.0.0-3
- Backport bidi patches

* Fri Oct 22 2021 Tom Stellard <tstellar@redhat.com> - 13.0.0-2
- Don't emit unwind tables for bpf

* Fri Oct 15 2021 Tom Stellard <tstellar@redhat.com> - 13.0.0-1
- 13.0.0 Release

* Fri Jul 16 2021 sguelton@redhat.com - 12.0.1-1
- 12.0.1 release

* Thu May 6 2021 sguelton@redhat.com - 12.0.0-1
- 12.0.0 release

* Thu Oct 29 2020 sguelton@redhat.com - 11.0.0-1
- 11.0.0 final release

* Thu Sep 17 2020 sguelton@redhat.com - 11.0.0-0.1.rc2
- 11.0.0-rc2 Release

* Fri Jul 24 2020 sguelton@redhat.com - 10.0.1-1
- 10.0.1 release

* Thu Apr 9 2020 sguelton@redhat.com - 10.0.0-1
- 10.0.0 final

* Fri Jan 10 2020 Tom Stellard <tstellar@redhat.com> - 9.0.1-2
- Fix crash with kernel bpf self-tests

* Thu Dec 19 2019 Tom Stellard <tstellar@redhat.com> - 9.0.1-1
- 9.0.1 Release

* Fri Nov 15 2019 Tom Stellard <tstellar@redhat.com> - 9.0.0-5
- Fix typo from previous patch: move clang-libs dep to correct sub-package

* Thu Nov 14 2019 Tom Stellard <tstellar@redhat.com> - 9.0.0-4
- Add explicit requires for clang-libs to fix rpmdiff errors

* Wed Oct 02 2019 Tom Stellard <tstellar@redhat.com> - 9.0.0-3
- Limit build to 8 threads to avoid OOM on x86_64

* Wed Oct 02 2019 Tom Stellard <tstellar@redhat.com> - 9.0.0-2
- Disable CLANG_LINK_CLANG_DYLIB

* Fri Sep 27 2019 Tom Stellard <tstellar@redhat.com> - 9.0.0-1
- 9.0.0 Release

* Thu Aug 1 2019 sguelton@redhat.com - 8.0.1-1
- 8.0.1 Release

* Thu Jun 13 2019 sguelton@redhat.com - 8.0.1-0.1.rc2
- 8.0.1rc2 Release

* Thu Apr 11 2019 sguelton@redhat.com - 8.0.0-1
- 8.0.0 Release

* Fri Dec 14 2018 Tom Stellard <tstellar@redhat.com> - 7.0.1-1
- 7.0.1-1 Release

* Mon Dec 10 2018 Tom Stellard <tstellar@redhat.com> - 7.0.1-0.1.rc3
- 7.0.1-rc3 Release

* Mon Nov 05 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-12
- User helper macro to fixup config.h for multilib

* Sat Oct 27 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-11
- Enable make check

* Mon Oct 15 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-10
- Remove Provides: llvm-toolset-6.0-clang-libs

* Fri Oct 12 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-9
- Add Provides: llvm-toolset-6.0-clang-libs

* Tue Oct 02 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-8
- Don't use python2 for the build

* Mon Oct 01 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-7
- Drop scl macros

* Tue Sep 25 2018 Tomas Orsava <torsava@redhat.com> - 6.0.1-6
- Change Requires from python3 to platform-python
- The python3 package was renamed to platform-python
- Related: rhbz#1619153

* Fri Sep 14 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-5
- Use python3 for git-clang-format

* Thu Sep 13 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-4
- Fix python dependencies

* Tue Aug 07 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-3
- Install ld.so.conf file in the root filesystem

* Thu Aug 02 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-2
- Remove annobin work-around

* Wed Jul 11 2018 Tom Stellard <tstellar@redhat.com> - 6.0.1-1
- 6.0.1 Release

* Wed Apr 11 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-7
- Add conditionals to enable building only the clang-libs package

* Fri Apr 06 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-6
- Use cmake from base RHEL

* Mon Mar 19 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-5
- Backport r310435 from clang trunk. rhbz#1558223

* Mon Mar 19 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-4
- Use system gcc instead of dts.

* Tue Feb 06 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-3
- Backport retpoline support

* Sat Jan 20 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-2
- Limit number of build threads on ppc64le to avoid OOM errors

* Tue Jan 09 2018 Tom Stellard <tstellar@redhat.com> - 5.0.1-1
- 5.0.1 Release

* Wed Jun 21 2017 Tom Stellard <tstellar@redhat.com> - 4.0.1-1
- 4.0.1 Release.

* Wed Jun 21 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-15
- Fix Requires for clang-tools-extra

* Wed Jun 21 2017 Tom Stellard <tstellar@redhat.com - 4.0.0-14
- Fix Requires for clang-tools-extra

* Tue Jun 20 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-13
- Drop libomp dependency on s390x

* Thu Jun 15 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-12
- Use libstdc++ from devtoolset-7

* Wed Jun 07 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-11
- Fix libomp requires

* Wed Jun 07 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-10
- Build for llvm-toolset-7 rename

* Tue May 30 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-9
- Use ld from devtoolset in clang toolchain

* Mon May 29 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-8
- Add dependency on libopenmp

* Thu May 25 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-7
- Fix check for gcc install

* Wed May 24 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-6
- Add devtoolset-6 dependency for newer libstdc++

* Fri May 12 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-5
- Add dependency on compiler-rt

* Tue May 02 2017 Tom Stellard <tstellar@redhat.com>
- Fix dependencies with scl

* Mon May 01 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-4
- Build with llvm-toolset-4

* Mon Mar 27 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-3
- Enable eh/rtti, which are required by lldb.

* Fri Mar 24 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-2
- Fix clang-tools-extra build
- Fix install

* Thu Mar 23 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-1
- clang 4.0.0 final release

* Mon Mar 20 2017 David Goerger <david.goerger@yale.edu> - 3.9.1-3
- add clang-tools-extra rhbz#1328091

* Thu Mar 16 2017 Tom Stellard <tstellar@redhat.com> - 3.9.1-2
- Enable build-id by default rhbz#1432403

* Thu Mar 02 2017 Dave Airlie <airlied@redhat.com> - 3.9.1-1
- clang 3.9.1 final release

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.9.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Mon Nov 14 2016 Nathaniel McCallum <npmccallum@redhat.com> - 3.9.0-3
- Add Requires: compiler-rt to clang-libs.
- Without this, compiling with certain CFLAGS breaks.

* Tue Nov  1 2016 Peter Robinson <pbrobinson@fedoraproject.org> 3.9.0-2
- Rebuild for new arches

* Fri Oct 14 2016 Dave Airlie <airlied@redhat.com> - 3.9.0-1
- clang 3.9.0 final release

* Fri Jul 01 2016 Stephan Bergmann <sbergman@redhat.com> - 3.8.0-2
- Resolves: rhbz#1282645 add GCC abi_tag support

* Thu Mar 10 2016 Dave Airlie <airlied@redhat.com> 3.8.0-1
- clang 3.8.0 final release

* Thu Mar 03 2016 Dave Airlie <airlied@redhat.com> 3.8.0-0.4
- clang 3.8.0rc3

* Wed Feb 24 2016 Dave Airlie <airlied@redhat.com> - 3.8.0-0.3
- package all libs into clang-libs.

* Wed Feb 24 2016 Dave Airlie <airlied@redhat.com> 3.8.0-0.2
- enable dynamic linking of clang against llvm

* Thu Feb 18 2016 Dave Airlie <airlied@redhat.com> - 3.8.0-0.1
- clang 3.8.0rc2

* Fri Feb 12 2016 Dave Airlie <airlied@redhat.com> 3.7.1-4
- rebuild against latest llvm packages
- add BuildRequires llvm-static

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 3.7.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Thu Jan 28 2016 Dave Airlie <airlied@redhat.com> 3.7.1-2
- just accept clang includes moving to /usr/lib64, upstream don't let much else happen

* Thu Jan 28 2016 Dave Airlie <airlied@redhat.com> 3.7.1-1
- initial build in Fedora.

* Tue Oct 06 2015 Jan Vcelak <jvcelak@fedoraproject.org> 3.7.0-100
- initial version using cmake build system
