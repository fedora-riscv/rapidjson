# Conditional for release and snapshot builds. Uncomment for release-builds.
%global rel_build	1

# Settings used for build from snapshots.
%if 0%{?rel_build}
%global gittar		%{name}-%{version}.tar.gz
%else  # 0%%{?rel_build}
%global commit		67143c2ba002604a510ba436a8ed0d785a9f7de6
%global commit_date	20140801
%global shortcommit	%(c=%{commit};echo ${c:0:7})
%global gitver		git%{commit_date}-%{shortcommit}
%global gitrel		.git%{commit_date}.%{shortcommit}
%global gittar		%{name}-%{version}-%{gitver}.tar.gz
%endif # 0%%{?rel_build}

# This is a header-only lib.  There is no debuginfo generated.
%global debug_package	%{nil}

# Set %%_pkgdocdir-helper-macro if not defined.
%if 0%{!?_pkgdocdir:1}
%global _pkgdocdir	%{_docdir}/%{name}-%{version}
%endif # 0%%{!?_pkgdocdir:1}

# CMake-builds go out-of-tree.  Tests are not run in %%{buildroot}.
%global cmake_build_dir	build-%{?__isa}%{?dist}

# Set %%giturl for later use.
%global giturl		https://github.com/miloyip/%{name}/archive

%global common_desc							\
RapidJSON is a fast JSON parser and generator for C++.  It was		\
inspired by RapidXml.							\
									\
  RapidJSON is small but complete.  It supports both SAX and DOM style	\
  API. The SAX parser is only a half thousand lines of code.		\
									\
  RapidJSON is fast.  Its performance can be comparable to strlen().	\
  It also optionally supports SSE2/SSE4.1 for acceleration.		\
									\
  RapidJSON is self-contained.  It does not depend on external		\
  libraries such as BOOST.  It even does not depend on STL.		\
									\
  RapidJSON is memory friendly.  Each JSON value occupies exactly	\
  16/20 bytes for most 32/64-bit machines (excluding text string).  By	\
  default it uses a fast memory allocator, and the parser allocates	\
  memory compactly during parsing.					\
									\
  RapidJSON is Unicode friendly.  It supports UTF-8, UTF-16, UTF-32	\
  (LE & BE), and their detection, validation and transcoding		\
  internally.  For example, you can read a UTF-8 file and let RapidJSON	\
  transcode the JSON strings into UTF-16 in the DOM.  It also supports	\
  surrogates and "\u0000" (null character).				\
									\
JSON(JavaScript Object Notation) is a light-weight data exchange	\
format.  RapidJSON should be in fully compliance with RFC4627/ECMA-404.

Name:		rapidjson
Version:	1.0.2
Release:	1%{?gitrel}%{?dist}
Summary:	Fast JSON parser and generator for C++

License:	MIT
URL:		http://miloyip.github.io/%{name}
%if 0%{?rel_build}
# Sources for release-builds.
Source0:	%{giturl}/v%{version}.tar.gz#/%{gittar}
%else  # 0%%{?rel_build}
# Sources for snapshot-builds.
Source0:	%{giturl}/%{commit}.tar.gz#/%{gittar}
%endif # 0%%{?rel_build}

# Downstream-patch for gtest.
Patch0:		rapidjson-1.0.2-do_not_include_gtest_src_dir.patch

BuildRequires:	cmake
BuildRequires:	gtest-devel
BuildRequires:	valgrind

%description
%{common_desc}


%package devel
Summary:	%{summary}
BuildArch:	noarch

Provides:	%{name}			== %{version}-%{release}
Provides:	%{name}-static		== %{version}-%{release}

%description devel
%{common_desc}

%files devel
%license license.txt
%doc %dir %{_pkgdocdir}
%doc %{_pkgdocdir}/CHANGELOG.md
%doc %{_pkgdocdir}/readme*.md
%{_datadir}/cmake
%{_datadir}/pkgconfig/*
%{_includedir}/%{name}


%package doc
Summary:	Documentation-files for %{name}
BuildArch:	noarch

BuildRequires:	%{_sbindir}/hardlink
BuildRequires:	doxygen

%description doc
This package contains the documentation-files for %{name}.

%files doc
# Pickup license-files from main-pkg's license-dir.
# If there's no license-dir they are picked up by %%doc previously.
%{?_licensedir:%license %{_datadir}/licenses/%{name}*}
%doc %{_pkgdocdir}


%prep
%setup -q%{!?rel_build:n %{name}-%{commit}}
%patch0 -p1 -b .gtest
%{__mkdir} -p %{cmake_build_dir}

# Fix 'W: wrong-file-end-of-line-encoding'.
for _file in "license.txt" $(%{_bindir}/find example -type f -name '*.c*')
do
  %{__sed} -e 's!\r$!!g' < ${_file} > ${_file}.new &&			\
  /bin/touch -r ${_file} ${_file}.new &&				\
  %{__mv} -f ${_file}.new ${_file}
done

# Create an uncluttered backup of examples for inclusion in %%doc.
%{__cp} -a example examples

# Disable -Werror.
%{_bindir}/find . -type f -name 'CMakeLists.txt' -print0 |			\
	%{_bindir}/xargs -0 %{__sed} -i -e's![ \t]*-Werror!!g'


%build
pushd %{cmake_build_dir}
%cmake									\
	-DDOC_INSTALL_DIR=%{_pkgdocdir}					\
	-DGTESTSRC_FOUND=TRUE						\
	-DGTEST_SOURCE_DIR=.						\
	..
%{__make} %{?_smp_mflags}
popd


%install
pushd %{cmake_build_dir}
%{__make} install DESTDIR=%{buildroot}
popd

# Move pkgconfig und CMake-stuff to generic datadir.
%{__mv} -f %{buildroot}%{_libdir}/* %{buildroot}%{_datadir}

# Copy the documentation-files to final location.
%{__cp} -a CHANGELOG.md readme*.md examples %{buildroot}%{_pkgdocdir}

# Find and purge build-sys files.
%{_bindir}/find %{buildroot} -type f -name 'CMake*.txt' -print0 |	\
	%{_bindir}/xargs -0 %{__rm} -fv

# Hardlink duplicated files to save space.
%{_sbindir}/hardlink -v %{buildroot}%{_includedir}
%{_sbindir}/hardlink -v %{buildroot}%{_pkgdocdir}


%check
# Valgrind fails on %%ix86.
%ifarch %{ix86}
CTEST_EXCLUDE=".*valgrind.*"
%endif # arch %%{ix86}
pushd %{cmake_build_dir}
%{_bindir}/ctest -E "${CTEST_EXCLUDE}" -V .
popd


%changelog
* Sun Apr 03 2016 Björn Esser <fedora@besser82.io> - 1.0.2-1
- update to latest upstream-release (#1322941)

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.12-0.4.git20140801.67143c2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Thu Jun 18 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.12-0.3.git20140801.67143c2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.12-0.2.git20140801.67143c2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Wed Aug 06 2014 Björn Esser <bjoern.esser@gmail.com> - 0.12-0.1.git20140801.67143c2
- initial rpm release (#1127380)
