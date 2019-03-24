Name:		toggl2pl
Version:	1.0.0
Release:	1%{?dist}
Summary:	Tool to simplify import of time entries from Toggl into Project Laboratory

License:	MIT
URL:		https://git-y.yourserveradmin.com/pa/toggl2pl
Source0:	%{name}-%{version}.tar.gz

BuildArch:	x86_64
BuildRequires:	gcc python-virtualenv rpm-build

AutoReq:	no

Packager:	Andrew Poltavchenko <pa@yourserveradmin.com>
Vendor:		YourServerAdmin.COM

%description
%{summary}.

%prep
%setup -q
virtualenv --python=python3 venv

%build
source venv/bin/activate
pip install -r requirements.txt
pyinstaller \
  --onefile \
  --name=%{name} \
  scripts/%{name}

%install
install -v -D -m 0755 dist/%{name} %{buildroot}%{_bindir}/%{name}

%files
%defattr(-,root,root)
%{_bindir}/%{name}

