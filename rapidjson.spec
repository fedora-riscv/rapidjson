# Conditional for release and snapshot builds. Uncomment for release-builds.
#global rel_build 1

# Set %%test_config to release / debug for testsuite.
#global test_config debug
%global test_config release

# Settings used for build from snapshots.
%{!?rel_build:%global commit		67143c2ba002604a510ba436a8ed0d785a9f7de6}
%{!?rel_build:%global commit_date	20140801}
%{!?rel_build:%global shortcommit	%(c=%{commit};echo ${c:0:7})}
%{!?rel_build:%global gitver		git%{commit_date}-%{shortcommit}}
%{!?rel_build:%global gitrel		.git%{commit_date}.%{shortcommit}}
%{!?rel_build:%global gittar		%{name}-%{version}-%{gitver}.tar.gz}
%{?rel_build: %global gittar		%{name}-%{version}.tar.gz}

# This is a header-only lib.  There is no debuginfo generated.
%global debug_package %{nil}

# Set %%_pkgdocdir-helper-macro if not defined.
%{!?_pkgdocdir:%global _pkgdocdir %{_docdir}/%{name}-%{version}}

# Set %%giturl for later use.
%global giturl https://github.com/miloyip/%{name}/archive

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

Name:			rapidjson
Version:		0.12
Release:		0.4%{?gitrel}%{?dist}
Summary:		Fast JSON parser and generator for C++

License:		MIT
URL:			http://miloyip.github.io/%{name}
# Sources for release-builds.
%{?rel_build:Source0:	%{giturl}/v%{version}.tar.gz#/%{gittar}}
# Sources for snapshot-builds.
%{!?rel_build:Source0:	%{giturl}/%{commit}.tar.gz#/%{gittar}}

# Accepted upstream.  See: https://code.google.com/p/rapidjson/issues/detail?id=20
Patch0:			https://rapidjson.googlecode.com/issues/attachment?aid=200000000&name=generic_stream.patch&token=ABZ6GAepvWgj_soBAqcTKLtzL3jD3_hObg%3A1407342581907#/rapidjson-0.12_genericstream.patch

BuildRequires:		premake
BuildRequires:		valgrind

%description
%{common_desc}


%package devel
Summary:		%{summary}
BuildArch:		noarch

Provides:		%{name}			== %{version}-%{release}
Provides:		%{name}-static		== %{version}-%{release}

%description devel
%{common_desc}

%files devel
%doc %dir %{_pkgdocdir}
%doc %{_pkgdocdir}/license.txt
%{_includedir}/%{name}


%package doc
Summary:		Documentation-files for %{name}
BuildArch:		noarch

BuildRequires:		%{_sbindir}/hardlink
BuildRequires:		doxygen

%description doc
This package contains the documentation-files for %{name}.

%files doc
%doc %{_pkgdocdir}


%prep
%setup -q%{!?rel_build:n %{name}-%{commit}}
%patch0

# Fix 'W: wrong-file-end-of-line-encoding'.
for _file in "license.txt" $(find example -type f -name '*.c*')
do
  %{__sed} -e 's!\r$!!g' < ${_file} > ${_file}.new &&			\
  %{_bindir}/touch -r ${_file} ${_file}.new &&				\
  %{__mv} -f ${_file}.new ${_file}
done

# Create an uncluttered backup of examples for inclusion in %%doc.
%{__cp} -a example examples

# Create dummy-configure.
echo '#!%{_bindir}/bash' > configure && %{__chmod} +x configure


%build
# Testsuite is not buildable on %%arm currently…
%ifarch %{ix86} x86_64
%configure
pushd build
%{_bindir}/premake4 'gmake'
popd
%{__make} %{?_smp_mflags} -C build/gmake -f test.make			\
	config=%{?test_config}%{?__isa_bits} verbose=1
%{__make} %{?_smp_mflags} -C build/gmake -f example.make		\
	config=%{?test_config}%{?__isa_bits} verbose=1
%endif # arch %%{ix86} x86_64
%{_bindir}/doxygen build/Doxyfile


%install
# There is no install-target in Makefile.
%{__mkdir_p} %{buildroot}%{_includedir} %{buildroot}%{_pkgdocdir}
%{__cp} -a include/* %{buildroot}%{_includedir}

# Copy the documentation-files to final location.
%{__cp} -a license.txt readme.md doc/*.md doc/html examples		\
	%{buildroot}%{_pkgdocdir}

# Hardlink duplicated files to save space.
%{_sbindir}/hardlink -v %{buildroot}%{_includedir}
%{_sbindir}/hardlink -v %{buildroot}%{_pkgdocdir}


%check
# Testsuite is not buildable on %%arm currently…
%ifarch %{ix86} x86_64
pushd bin
./perftest_%{?test_config}_x%{?__isa_bits}_gmake
./unittest_%{?test_config}_x%{?__isa_bits}_gmake || :
%{_bindir}/valgrind	--verbose					\
			--leak-check=full				\
			--show-leak-kinds=all				\
			--error-exitcode=1				\
	./unittest_%{?test_config}_x%{?__isa_bits}_gmake || :
popd
%endif # arch %%{ix86} x86_64


%changelog
* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.12-0.4.git20140801.67143c2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Thu Jun 18 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.12-0.3.git20140801.67143c2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.12-0.2.git20140801.67143c2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Wed Aug 06 2014 Björn Esser <bjoern.esser@gmail.com> - 0.12-0.1.git20140801.67143c2
- initial rpm release (#1127380)
