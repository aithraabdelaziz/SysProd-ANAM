### Install GDAL (for geospatial data processing)
sudo apt update
sudo apt install -y gdal-bin libgdal-dev

# Add GDAL to the dynamic linker library path
echo 'export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

### Install PostgreSQL
# Update package list
sudo apt update

# Install PostgreSQL 16
sudo apt install -y postgresql-16

# Install PostGIS extension for PostgreSQL 16 (spatial database support)
sudo apt install -y postgresql-16-postgis-3

### Install unzip utility (used for extracting compressed files)
sudo apt install -y unzip

### Install dependencies required for WeasyPrint (PDF generation)
sudo apt install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libglib2.0-0 \
    libxml2 \
    libxslt1.1

### Install Python 3.11 (latest stable version)
# Install tools for managing repositories
sudo apt install -y software-properties-common

# Add the deadsnakes PPA (provides newer Python versions)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.11 and its virtual environment module
sudo apt install -y python3.11 python3.11-venv

### Create and activate a virtual environment named "cfenv"
python3.11 -m venv cfenv
source cfenv/bin/activate

### Install Python dependencies from the requirements file
pip install -r requirementsANAM.txt

### Run project setup
# Apply migrations
python manage.py migrate

# Collect static files (optional, for production)
# python manage.py collectstatic --noinput

# Create superuser (interactive)
python manage.py createsuperuser

# Run the development server
python manage.py runserver ##Starting Django development server on http://127.0.0.1:8000/
