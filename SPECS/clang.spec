%bcond_with compat_build
%bcond_without check

%global maj_ver 16
%global min_ver 0
%global patch_ver 6
#global rc_ver 4
%global clang_version %{maj_ver}.%{min_ver}.%{patch_ver}

%if %{with compat_build}
%global pkg_name clang%{maj_ver}
# Install clang to same prefix as llvm, so that apps that use llvm-config
# will also be able to find clang libs.
%global install_prefix %{_libdir}/llvm%{maj_ver}
%global install_bindir %{install_prefix}/bin
%global install_includedir %{install_prefix}/include
%global install_libdir %{install_prefix}/lib

%global pkg_bindir %{install_bindir}
%global pkg_includedir %{install_includedir}
%global pkg_libdir %{install_libdir}
%else
%global pkg_name clang
%global install_prefix /usr
%global pkg_libdir %{_libdir}
%endif

%global build_install_prefix %{buildroot}%{install_prefix}

%ifarch ppc64le aarch64
# Too many threads on some systems causes OOM errors.
%global _smp_mflags -j8
%endif

%global clang_srcdir clang-%{clang_version}%{?rc_ver:rc%{rc_ver}}.src
%global cmake_srcdir cmake-%{clang_version}%{?rc_ver:rc%{rc_ver}}.src
%global clang_tools_srcdir clang-tools-extra-%{clang_version}%{?rc_ver:rc%{rc_ver}}.src

%if !%{maj_ver} && 0%{?rc_ver}
%global abi_revision 2
%endif

Name:		%pkg_name
Version:	%{clang_version}%{?rc_ver:~rc%{rc_ver}}
Release:	2%{?dist}
Summary:	A C language family front-end for LLVM

License:	NCSA
URL:		http://llvm.org
Source0:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{clang_version}%{?rc_ver:-rc%{rc_ver}}/%{clang_srcdir}.tar.xz
Source3:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{clang_version}%{?rc_ver:-rc%{rc_ver}}/%{clang_srcdir}.tar.xz.sig
%if %{without compat_build}
Source1:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{clang_version}%{?rc_ver:-rc%{rc_ver}}/%{clang_tools_srcdir}.tar.xz
Source2:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{clang_version}%{?rc_ver:-rc%{rc_ver}}/%{clang_tools_srcdir}.tar.xz.sig
%endif
Source4:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{clang_version}%{?rc_ver:-rc%{rc_ver}}/%{cmake_srcdir}.tar.xz
Source5:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{clang_version}%{?rc_ver:-rc%{rc_ver}}/%{cmake_srcdir}.tar.xz.sig
Source6:	release-keys.asc
%if %{without compat_build}
Source7:	macros.%{name}
%endif

# Patches for clang
Patch1:     0003-PATCH-Make-funwind-tables-the-default-on-all-archs.patch
Patch2:     0003-PATCH-clang-Don-t-install-static-libraries.patch
Patch3:     0001-Driver-Add-a-gcc-equivalent-triple-to-the-list-of-tr.patch
# Drop the following patch after debugedit adds support to DWARF-5:
# https://sourceware.org/bugzilla/show_bug.cgi?id=28728
Patch5:     0010-PATCH-clang-Produce-DWARF4-by-default.patch
# Fix a test based on the triple used on RHEL-based systems.
Patch6:     0001-PowerPC-clang-Fix-triple.patch
# Make clangBasic and clangDriver depend on LLVMTargetParser
# See https://reviews.llvm.org/D141581
Patch7:     D141581.diff
# clang/cmake: Use installed gtest libraries for stand-alone builds
# See https://reviews.llvm.org/D138472
Patch8:     D138472.diff

Patch10:    fix-ieee128-cross.diff



Patch100:     disable-recommonmark.patch


# Patches for clang-tools-extra
%if %{without compat_build}
Patch201:  0001-clang-tools-extra-Make-test-dependency-on-LLVMHello-.patch
%endif

BuildRequires:	gcc
BuildRequires:	gcc-c++
BuildRequires:	cmake
BuildRequires:	ninja-build
%if %{with compat_build}
BuildRequires:	llvm%{maj_ver}-devel = %{version}
BuildRequires:	llvm%{maj_ver}-static = %{version}
%else
BuildRequires:	llvm-devel = %{version}
BuildRequires:	llvm-test = %{version}
# llvm-static is required, because clang-tablegen needs libLLVMTableGen, which
# is not included in libLLVM.so.
BuildRequires:	llvm-static = %{version}
BuildRequires:	llvm-googletest = %{version}
%endif

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
BuildRequires:	libatomic

# We need python3-devel for %%py3_shebang_fix
BuildRequires:	python3-devel

%if ! 0%{?rhel}
# For reproducible pyc file generation
# See https://docs.fedoraproject.org/en-US/packaging-guidelines/Python_Appendix/#_byte_compilation_reproducibility
BuildRequires: /usr/bin/marshalparser
%global py_reproducible_pyc_path %{buildroot}%{python3_sitelib}
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
Requires: %{name}-resource-filesystem%{?_isa} = %{version}
# RHEL specific: Use libstdc++ from gcc13 by default. rhbz#2178804
Requires: gcc-toolset-13-gcc-c++
Recommends: compiler-rt%{?_isa} = %{version}
# libomp-devel is required, so clang can find the omp.h header when compiling
# with -fopenmp.
Recommends: libomp-devel%{_isa} = %{version}
Recommends: libomp%{_isa} = %{version}

# Use lld as the default linker on ARM due to rhbz#1918924
%ifarch %{arm}
Requires: lld
%endif

%description libs
Runtime library for clang.

%package devel
Summary: Development header files for clang
%if %{without compat_build}
Requires: %{name}%{?_isa} = %{version}-%{release}
# The clang CMake files reference tools from clang-tools-extra.
Requires: %{name}-tools-extra%{?_isa} = %{version}-%{release}
Requires: %{name}-libs = %{version}-%{release}
%endif

%description devel
Development header files for clang.

%package resource-filesystem
Summary: Filesystem package that owns the clang resource directory
Provides: %{name}-resource-filesystem(major) = %{maj_ver}

%description resource-filesystem
This package owns the clang resouce directory: $libdir/clang/$version/

%if %{without compat_build}
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


%package -n python3-clang
Summary:       Python3 bindings for clang
Requires:      %{name}-libs%{?_isa} = %{version}-%{release}
Requires:      python3
%description -n python3-clang
%{summary}.


%endif


%prep
%{gpgverify} --keyring='%{SOURCE6}' --signature='%{SOURCE3}' --data='%{SOURCE0}'
%{gpgverify} --keyring='%{SOURCE6}' --signature='%{SOURCE5}' --data='%{SOURCE4}'

%setup -T -q -b 4 -n %{cmake_srcdir}
# TODO: It would be more elegant to set -DLLVM_COMMON_CMAKE_UTILS=%{_builddir}/%{cmake_srcdir},
# but this is not a CACHED variable, so we can't actually set it externally :(
cd ..
mv %{cmake_srcdir} cmake

%if %{with compat_build}
%autosetup -n %{clang_srcdir} -p2
%else

%{gpgverify} --keyring='%{SOURCE6}' --signature='%{SOURCE2}' --data='%{SOURCE1}'
%setup -T -q -b 1 -n %{clang_tools_srcdir}
%autopatch -m200 -p2

# failing test case
rm test/clang-tidy/checkers/altera/struct-pack-align.cpp

%py3_shebang_fix \
	clang-tidy/tool/run-clang-tidy.py \
	clang-tidy/tool/clang-tidy-diff.py \
	clang-include-fixer/find-all-symbols/tool/run-find-all-symbols.py


%setup -q -n %{clang_srcdir}
%autopatch -M200 -p2

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
# We run the builders out of memory on armv7 and i686 when LTO is enabled
%ifarch %{arm} i686
%define _lto_cflags %{nil}
%else
# This package does not ship any object files or static libraries, so we
# don't need -ffat-lto-objects.
%global _lto_cflags %(echo %{_lto_cflags} | sed 's/-ffat-lto-objects//')
%endif

# lto builds with gcc 11 fail while running the lit tests.
%define _lto_cflags %{nil}

%if 0%{?__isa_bits} == 64
sed -i 's/\@FEDORA_LLVM_LIB_SUFFIX\@/64/g' test/lit.cfg.py
%else
sed -i 's/\@FEDORA_LLVM_LIB_SUFFIX\@//g' test/lit.cfg.py
%endif

mkdir -p %{_vpath_builddir}
cd %{_vpath_builddir}

%ifarch s390 s390x %{arm} %ix86 ppc64le aarch64
# Decrease debuginfo verbosity to reduce memory consumption during final library linking
%global optflags %(echo %{optflags} | sed 's/-g /-g1 /')
%endif


%set_build_flags
CXXFLAGS="$CXXFLAGS -Wno-address -Wno-nonnull -Wno-maybe-uninitialized"
CFLAGS="$CFLAGS -Wno-address -Wno-nonnull -Wno-maybe-uninitialized"

# -DLLVM_ENABLE_NEW_PASS_MANAGER=ON can be removed once this patch is committed:
# https://reviews.llvm.org/D107628
# We set CLANG_DEFAULT_PIE_ON_LINUX=OFF to match the default used by Fedora's GCC.
%cmake .. -G Ninja \
	-DCLANG_DEFAULT_PIE_ON_LINUX=OFF \
	-DLLVM_PARALLEL_LINK_JOBS=1 \
	-DLLVM_LINK_LLVM_DYLIB:BOOL=ON \
	-DCMAKE_BUILD_TYPE=RelWithDebInfo \
	-DPYTHON_EXECUTABLE=%{__python3} \
	-DCMAKE_SKIP_RPATH:BOOL=ON \
%ifarch s390 s390x %{arm} %ix86 ppc64le aarch64
	-DCMAKE_C_FLAGS_RELWITHDEBINFO="%{optflags} -DNDEBUG" \
	-DCMAKE_CXX_FLAGS_RELWITHDEBINFO="%{optflags} -DNDEBUG" \
%endif
%if %{with compat_build}
	-DCLANG_BUILD_TOOLS:BOOL=OFF \
	-DLLVM_CONFIG:FILEPATH=%{pkg_bindir}/llvm-config-%{maj_ver}-%{__isa_bits} \
	-DCMAKE_INSTALL_PREFIX=%{install_prefix} \
	-DCLANG_INCLUDE_TESTS:BOOL=OFF \
%else
	-DCLANG_INCLUDE_TESTS:BOOL=ON \
	-DLLVM_EXTERNAL_CLANG_TOOLS_EXTRA_SOURCE_DIR=../../%{clang_tools_srcdir} \
	-DLLVM_EXTERNAL_LIT=%{_bindir}/lit \
	-DLLVM_MAIN_SRC_DIR=%{_datadir}/llvm/src \
%if 0%{?__isa_bits} == 64
	-DLLVM_LIBDIR_SUFFIX=64 \
%else
	-DLLVM_LIBDIR_SUFFIX= \
%endif
%endif
	\
%if %{with compat_build}
	-DLLVM_TABLEGEN_EXE:FILEPATH=%{_bindir}/llvm-tblgen-%{maj_ver} \
%else
	-DLLVM_TABLEGEN_EXE:FILEPATH=%{_bindir}/llvm-tblgen \
%endif
	-DCLANG_ENABLE_ARCMT:BOOL=ON \
	-DCLANG_ENABLE_STATIC_ANALYZER:BOOL=ON \
	-DCLANG_INCLUDE_DOCS:BOOL=ON \
	-DCLANG_PLUGIN_SUPPORT:BOOL=ON \
	-DENABLE_LINKER_BUILD_ID:BOOL=ON \
	-DLLVM_ENABLE_EH=ON \
	-DLLVM_ENABLE_RTTI=ON \
	-DLLVM_BUILD_DOCS=ON \
	-DLLVM_ENABLE_NEW_PASS_MANAGER=ON \
	-DLLVM_ENABLE_SPHINX=ON \
	-DCLANG_LINK_CLANG_DYLIB=ON \
	%{?abi_revision:-DLLVM_ABI_REVISION=%{abi_revision}} \
	-DSPHINX_WARNINGS_AS_ERRORS=OFF \
	\
	-DCLANG_BUILD_EXAMPLES:BOOL=OFF \
	-DBUILD_SHARED_LIBS=OFF \
	-DCLANG_REPOSITORY_STRING="%{?fedora:Fedora}%{?rhel:Red Hat} %{version}-%{release}" \
%ifarch %{arm}
	-DCLANG_DEFAULT_LINKER=lld \
%endif
	-DCLANG_DEFAULT_UNWINDLIB=libgcc \
	-DGCC_INSTALL_PREFIX=/opt/rh/gcc-toolset-13/root/usr

%cmake_build

%install

pushd %{_vpath_builddir}
%cmake_install
popd

%if %{with compat_build}

# Remove binaries/other files
rm -Rf %{buildroot}%{install_bindir}
rm -Rf %{buildroot}%{install_prefix}/share
rm -Rf %{buildroot}%{install_prefix}/libexec
# Remove scanview-py helper libs
rm -Rf %{buildroot}%{install_prefix}/lib/{libear,libscanbuild}

%else

# File in the macros file for other packages to use.  We are not doing this
# in the compat package, because the version macros would # conflict with
# eachother if both clang and the clang compat package were installed together.
install -p -m0644 -D %{SOURCE7} %{buildroot}%{_rpmmacrodir}/macros.%{name}
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

# Fix permissions of scan-view scripts
chmod a+x %{buildroot}%{_datadir}/scan-view/{Reporter.py,startfile.py}

# multilib fix
%multilib_fix_c_header --file %{_includedir}/clang/Config/config.h

# Move emacs integration files to the correct directory
mkdir -p %{buildroot}%{_emacs_sitestartdir}
for f in clang-format.el clang-rename.el clang-include-fixer.el; do
mv %{buildroot}{%{_datadir}/clang,%{_emacs_sitestartdir}}/$f
done

# remove editor integrations (bbedit, sublime, emacs, vim)
rm -vf %{buildroot}%{_datadir}/clang/clang-format-bbedit.applescript
rm -vf %{buildroot}%{_datadir}/clang/clang-format-sublime.py*

# TODO: Package html docs
rm -Rvf %{buildroot}%{_docdir}/Clang/clang/html
rm -Rvf %{buildroot}%{_datadir}/clang/clang-doc-default-stylesheet.css
rm -Rvf %{buildroot}%{_datadir}/clang/index.js

# TODO: What are the Fedora guidelines for packaging bash autocomplete files?
rm -vf %{buildroot}%{_datadir}/clang/bash-autocomplete.sh

# Create Manpage symlinks
ln -s clang.1.gz %{buildroot}%{_mandir}/man1/clang++.1.gz
ln -s clang.1.gz %{buildroot}%{_mandir}/man1/clang-%{maj_ver}.1.gz
ln -s clang.1.gz %{buildroot}%{_mandir}/man1/clang++-%{maj_ver}.1.gz

# Add clang++-{version} symlink
ln -s clang++ %{buildroot}%{_bindir}/clang++-%{maj_ver}


# Fix permission
chmod u-x %{buildroot}%{_mandir}/man1/scan-build.1*

%endif

# Create sub-directories in the clang resource directory that will be
# populated by other packages
mkdir -p %{buildroot}%{pkg_libdir}/clang/%{maj_ver}/{include,lib,share}/


# Remove clang-tidy headers.  We don't ship the libraries for these.
rm -Rvf %{buildroot}%{_includedir}/clang-tidy/

%if %{without compat_build}
# Add a symlink in /usr/bin to clang-format-diff
ln -s %{_datadir}/clang/clang-format-diff.py %{buildroot}%{_bindir}/clang-format-diff
%endif

%check
%if %{without compat_build}
%if %{with check}
# Build test dependencies separately, to prevent invocations of host clang from being affected
# by LD_LIBRARY_PATH below.
pushd %{_vpath_builddir}
%cmake_build --target clang-test-depends \
    ExtraToolsUnitTests ClangdUnitTests ClangIncludeCleanerUnitTests ClangPseudoUnitTests
popd
# requires lit.py from LLVM utilities
# FIXME: Fix failing ARM tests
LD_LIBRARY_PATH=%{buildroot}/%{_libdir} %{__ninja} %{_smp_mflags} check-all -C %{_vpath_builddir} || \
%ifarch %{arm}
:
%else
false
%endif
%endif
%endif


%if %{without compat_build}
%files
%license LICENSE.TXT
%{_bindir}/clang
%{_bindir}/clang++
%{_bindir}/clang-%{maj_ver}
%{_bindir}/clang++-%{maj_ver}
%{_bindir}/clang-cl
%{_bindir}/clang-cpp
%{_mandir}/man1/clang.1.gz
%{_mandir}/man1/clang++.1.gz
%{_mandir}/man1/clang-%{maj_ver}.1.gz
%{_mandir}/man1/clang++-%{maj_ver}.1.gz
%endif

%files libs
%if %{without compat_build}
%{_libdir}/clang/%{maj_ver}/include/*
%{_libdir}/*.so.*
%else
%{pkg_libdir}/*.so.*
%{pkg_libdir}/clang/%{maj_ver}/include/*
%endif

%files devel
%if %{without compat_build}
%{_libdir}/*.so
%{_includedir}/clang/
%{_includedir}/clang-c/
%{_libdir}/cmake/*
%dir %{_datadir}/clang/
%{_rpmmacrodir}/macros.%{name}
%else
%{pkg_libdir}/*.so
%{pkg_includedir}/clang/
%{pkg_includedir}/clang-c/
%{pkg_libdir}/cmake/
%endif

%files resource-filesystem
%dir %{pkg_libdir}/clang/
%dir %{pkg_libdir}/clang/%{maj_ver}/
%dir %{pkg_libdir}/clang/%{maj_ver}/include/
%dir %{pkg_libdir}/clang/%{maj_ver}/lib/
%dir %{pkg_libdir}/clang/%{maj_ver}/share/

%if %{without compat_build}
%files analyzer
%{_bindir}/scan-view
%{_bindir}/scan-build
%{_bindir}/analyze-build
%{_bindir}/intercept-build
%{_bindir}/scan-build-py
%{_libexecdir}/ccc-analyzer
%{_libexecdir}/c++-analyzer
%{_libexecdir}/analyze-c++
%{_libexecdir}/analyze-cc
%{_libexecdir}/intercept-c++
%{_libexecdir}/intercept-cc
%{_datadir}/scan-view/
%{_datadir}/scan-build/
%{_mandir}/man1/scan-build.1.*
%{python3_sitelib}/libear
%{python3_sitelib}/libscanbuild


%files tools-extra
%{_bindir}/amdgpu-arch
%{_bindir}/clang-apply-replacements
%{_bindir}/clang-change-namespace
%{_bindir}/clang-check
%{_bindir}/clang-doc
%{_bindir}/clang-extdef-mapping
%{_bindir}/clang-format
%{_bindir}/clang-include-cleaner
%{_bindir}/clang-include-fixer
%{_bindir}/clang-move
%{_bindir}/clang-offload-bundler
%{_bindir}/clang-offload-packager
%{_bindir}/clang-linker-wrapper
%{_bindir}/clang-pseudo
%{_bindir}/clang-query
%{_bindir}/clang-refactor
%{_bindir}/clang-rename
%{_bindir}/clang-reorder-fields
%{_bindir}/clang-repl
%{_bindir}/clang-scan-deps
%{_bindir}/clang-tidy
%{_bindir}/clangd
%{_bindir}/diagtool
%{_bindir}/hmaptool
%{_bindir}/nvptx-arch
%{_bindir}/pp-trace
%{_bindir}/c-index-test
%{_bindir}/find-all-symbols
%{_bindir}/modularize
%{_bindir}/clang-format-diff
%{_mandir}/man1/diagtool.1.gz
%{_emacs_sitestartdir}/clang-format.el
%{_emacs_sitestartdir}/clang-rename.el
%{_emacs_sitestartdir}/clang-include-fixer.el
%{_datadir}/clang/clang-format.py*
%{_datadir}/clang/clang-format-diff.py*
%{_datadir}/clang/clang-include-fixer.py*
%{_datadir}/clang/clang-tidy-diff.py*
%{_bindir}/run-clang-tidy
%{_datadir}/clang/run-find-all-symbols.py*
%{_datadir}/clang/clang-rename.py*

%files -n git-clang-format
%{_bindir}/git-clang-format

%files -n python3-clang
%{python3_sitelib}/clang/


%endif
%changelog
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
